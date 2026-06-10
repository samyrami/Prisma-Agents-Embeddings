"""
Pipeline de ingesta: docs → texto → chunks → embeddings → FAISS → S3.

Flujo de `run_ingest`:
  1. Lista los docs fuente (S3: agents/<id>/docs/, o carpeta local).
  2. Lee metadata opcional del sidecar docs.json (title/tag/instructor_only/
     always_include por archivo).
  3. Extrae texto; los docs always_include van ENTEROS a chunks.json (sin
     embedding); el resto se chunkea y embebe en batch.
  4. Publica index.faiss + chunks.json + manifest.json en
     agents/<id>/vector_store/vN/ (N = próxima versión libre — las versiones
     son INMUTABLES, nunca se sobreescriben).
  5. --activate: actualiza config.json para apuntar a la versión nueva. El
     runtime la recoge al expirar su TTL, sin reinicio.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from westfield_agent_ingest.chunking import chunk_text, normalize_text
from westfield_agent_ingest.contracts import (
    AlwaysIncludeDoc,
    ChunkingParams,
    ChunkMeta,
    DocMeta,
    DocsSidecar,
    RetrievalDefaults,
    SourceDoc,
    VectorStoreManifest,
)
from westfield_agent_ingest.faiss_builder import build_faiss_bytes
from westfield_agent_ingest.readers import extract_text, is_supported
from westfield_agent_ingest.s3_io import (
    ObjectNotFoundError,
    ObjectStore,
    next_vector_store_version,
    put_json,
    read_agent_config,
    write_agent_config,
)

SIDECAR_FILE = "docs.json"


class Embedder(Protocol):
    """Lo implementan embeddings.OpenAIEmbeddings y los fakes de test."""

    model: str

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class SourceDocument:
    """Un doc fuente ya leído, con su metadata resuelta."""

    meta: DocMeta
    data: bytes


@dataclass
class IngestResult:
    agent_id: str
    version: str
    chunk_count: int
    always_include_count: int
    activated: bool
    vector_store_s3_uri: str


def run_ingest(
    store: ObjectStore,
    embedder: Embedder,
    agent_id: str,
    *,
    prefix: str = "agents",
    source: str = "s3",
    docs_dir: str | Path | None = None,
    chunk_size: int = 1000,
    overlap: int = 100,
    version: str | None = None,
    activate: bool = True,
    embedding_provider: str = "openai",
) -> IngestResult:
    """
    raises ObjectNotFoundError si el agente no tiene config.json (correr
    `ingest scaffold` primero), ValueError si no hay docs procesables o la
    versión pedida ya existe.
    """
    # El config debe existir ANTES de ingestar — el scaffold lo crea.
    config = read_agent_config(store, prefix, agent_id)

    documents = (
        _load_docs_from_local(Path(docs_dir))
        if source == "local"
        else _load_docs_from_s3(store, f"{prefix}/{agent_id}/docs/")
    )
    if not documents:
        raise ValueError(
            f"El agente '{agent_id}' no tiene docs procesables "
            f"({'carpeta ' + str(docs_dir) if source == 'local' else 's3 docs/'})."
        )

    # ---- extraer texto y separar always_include de chunkeables ----
    chunks: list[ChunkMeta] = []
    chunk_texts: list[str] = []
    always_include: list[AlwaysIncludeDoc] = []
    source_docs: list[SourceDoc] = []

    for doc in documents:
        meta = doc.meta
        text = extract_text(meta.file, doc.data)
        if not text.strip():
            continue
        source_docs.append(
            SourceDoc(
                doc_file=meta.file,
                doc_title=meta.title,
                doc_tag=meta.tag,
                instructor_only=meta.instructor_only,
            )
        )
        if meta.always_include:
            always_include.append(
                AlwaysIncludeDoc(
                    doc_file=meta.file,
                    doc_title=meta.title,
                    doc_tag=meta.tag,
                    instructor_only=meta.instructor_only,
                    text=normalize_text(text),
                )
            )
            continue
        for i, piece in enumerate(chunk_text(text, size=chunk_size, overlap=overlap)):
            chunks.append(
                ChunkMeta(
                    id=f"{meta.file}#{i}",
                    doc_file=meta.file,
                    doc_title=meta.title,
                    doc_tag=meta.tag,
                    instructor_only=meta.instructor_only,
                    text=piece,
                )
            )
            chunk_texts.append(piece)

    if not chunks:
        raise ValueError(
            f"El agente '{agent_id}' no produjo chunks (¿todos los docs son always_include?)."
        )

    # ---- embeddings + FAISS ----
    vectors = embedder.embed_batch(chunk_texts)
    if len(vectors) != len(chunks):
        raise RuntimeError(f"Embeddings devolvió {len(vectors)} vectores para {len(chunks)} chunks.")
    index_bytes = build_faiss_bytes(vectors)

    # ---- publicar versión inmutable ----
    new_version = version or next_vector_store_version(store, prefix, agent_id)
    vs_prefix = f"{prefix}/{agent_id}/vector_store/{new_version}"
    if store.exists(f"{vs_prefix}/manifest.json"):
        raise ValueError(f"La versión {new_version} ya existe — las versiones son inmutables.")

    manifest = VectorStoreManifest(
        vector_store_id=new_version,
        agent_id=agent_id,
        embedding_provider=embedding_provider,
        embedding_model=embedder.model,
        embedding_dimensions=len(vectors[0]),
        generated_at=datetime.now(UTC).isoformat(),
        chunk_count=len(chunks),
        chunking=ChunkingParams(chunk_size_chars=chunk_size, chunk_overlap_chars=overlap),
        retrieval_defaults=RetrievalDefaults(top_k=config.top_k, min_similarity=config.min_similarity),
        source_docs=source_docs,
    )
    store.put_bytes(f"{vs_prefix}/index.faiss", index_bytes)
    put_json(
        store,
        f"{vs_prefix}/chunks.json",
        {
            "chunks": [c.model_dump() for c in chunks],
            "always_include": [d.model_dump() for d in always_include],
        },
    )
    put_json(store, f"{vs_prefix}/manifest.json", manifest.model_dump())

    # ---- activar (read-modify-write del config.json) ----
    uri = f"s3://{store.bucket}/{vs_prefix}/"
    if activate:
        config.vector_store_id = new_version
        config.vector_store_s3_uri = uri
        write_agent_config(store, prefix, agent_id, config)

    return IngestResult(
        agent_id=agent_id,
        version=new_version,
        chunk_count=len(chunks),
        always_include_count=len(always_include),
        activated=activate,
        vector_store_s3_uri=uri,
    )


# ------------------------------------------------------------- carga de docs


def _resolve_meta(sidecar: DocsSidecar, filename: str) -> DocMeta:
    for meta in sidecar.docs:
        if meta.file == filename:
            return meta if meta.title else meta.model_copy(update={"title": filename})
    return DocMeta(file=filename, title=filename)


def _load_docs_from_s3(store: ObjectStore, docs_prefix: str) -> list[SourceDocument]:
    sidecar = DocsSidecar()
    with contextlib.suppress(ObjectNotFoundError):
        sidecar = DocsSidecar.model_validate_json(store.get_text(f"{docs_prefix}{SIDECAR_FILE}"))

    documents: list[SourceDocument] = []
    for key in sorted(store.list_keys(docs_prefix)):
        filename = key[len(docs_prefix) :]
        if not filename or filename == SIDECAR_FILE or not is_supported(filename):
            continue
        documents.append(
            SourceDocument(meta=_resolve_meta(sidecar, filename), data=store.get_bytes(key))
        )
    return documents


def _load_docs_from_local(docs_dir: Path) -> list[SourceDocument]:
    if not docs_dir or not docs_dir.is_dir():
        raise ValueError(f"Carpeta de docs inexistente: {docs_dir}")

    sidecar = DocsSidecar()
    sidecar_path = docs_dir / SIDECAR_FILE
    if sidecar_path.exists():
        sidecar = DocsSidecar.model_validate_json(sidecar_path.read_text(encoding="utf-8"))

    documents: list[SourceDocument] = []
    for path in sorted(docs_dir.iterdir()):
        if not path.is_file() or path.name == SIDECAR_FILE or not is_supported(path.name):
            continue
        documents.append(
            SourceDocument(meta=_resolve_meta(sidecar, path.name), data=path.read_bytes())
        )
    return documents
