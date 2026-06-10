"""
Migración del índice legacy del backend mono-agente (maia-index.json) al
contrato nuevo del runtime multi-agente — SIN re-embeber.

El índice legacy (generado por `npm run ingest` del proyecto Node) trae los
embeddings inline y ya L2-normalizados, así que van directo a un
IndexFlatIP. Los chunks/always_include mapean 1:1 descartando el campo
`embedding`.

Formato legacy esperado:
{
  "name": str, "embedding_model": str, "generated_at": str,
  "retrieval": {top_k, min_similarity, chunk_size_chars, chunk_overlap_chars},
  "always_include": [{doc_file, doc_title, doc_tag, instructor_only, text}],
  "chunks": [{id, doc_file, doc_title, doc_tag, instructor_only, text, embedding}]
}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from westfield_agent_ingest.contracts import (
    AgentConfigDoc,
    ChunkingParams,
    RetrievalDefaults,
    SourceDoc,
    VectorStoreManifest,
)
from westfield_agent_ingest.faiss_builder import build_faiss_bytes
from westfield_agent_ingest.s3_io import (
    ObjectNotFoundError,
    ObjectStore,
    next_vector_store_version,
    put_json,
    read_agent_config,
    write_agent_config,
)

# Marcadores anti-leak que vivían hardcodeados en el backend mono-agente —
# ahora son configuración del agente.
LEGACY_LEAK_MARKERS = [
    "Notas del instructor",
    "notas del profesor",
    "Vías de Respuesta",
    "Reflexiones que Puede Suscitar",
]

LEGACY_LEAK_REPLACEMENT = (
    "No puedo compartir el material interno del instructor. "
    "Volvamos a tu argumento: ¿qué evidencia concreta del caso lo sostiene?"
)

LEGACY_FALLBACK_MESSAGE = (
    "Estoy teniendo un problema técnico en este momento. "
    "Retomemos tu argumento en unos minutos."
)


@dataclass
class MigrateResult:
    agent_id: str
    version: str
    chunk_count: int
    always_include_count: int
    config_created: bool
    vector_store_s3_uri: str


def migrate_legacy(
    store: ObjectStore,
    agent_id: str,
    input_path: str | Path,
    *,
    prefix: str = "agents",
    system_prompt_file: str | Path | None = None,
    agent_name: str | None = None,
    llm_model: str = "gpt-4o-mini",
    activate: bool = True,
) -> MigrateResult:
    """
    Publica el índice legacy como vector_store/vN/ + prompt + config.json.

    raises ValueError si el índice legacy no tiene chunks con embeddings.
    """
    legacy = json.loads(Path(input_path).read_text(encoding="utf-8"))
    chunks_legacy = legacy.get("chunks") or []
    if not chunks_legacy:
        raise ValueError(f"El índice legacy {input_path} no tiene chunks.")

    vectors = [c["embedding"] for c in chunks_legacy]
    chunks = [
        {
            "id": c["id"],
            "doc_file": c["doc_file"],
            "doc_title": c["doc_title"],
            "doc_tag": c["doc_tag"],
            "instructor_only": bool(c.get("instructor_only", False)),
            "text": c["text"],
        }
        for c in chunks_legacy
    ]
    always_include = list(legacy.get("always_include") or [])
    retrieval = legacy.get("retrieval") or {}

    # ---- publicar vector store (versión inmutable) ----
    version = next_vector_store_version(store, prefix, agent_id)
    vs_prefix = f"{prefix}/{agent_id}/vector_store/{version}"
    uri = f"s3://{store.bucket}/{vs_prefix}/"

    manifest = VectorStoreManifest(
        vector_store_id=version,
        agent_id=agent_id,
        embedding_provider="openai",
        embedding_model=legacy.get("embedding_model", "text-embedding-3-small"),
        embedding_dimensions=len(vectors[0]),
        generated_at=legacy.get("generated_at", ""),
        chunk_count=len(chunks),
        chunking=ChunkingParams(
            chunk_size_chars=int(retrieval.get("chunk_size_chars", 0)),
            chunk_overlap_chars=int(retrieval.get("chunk_overlap_chars", 0)),
        ),
        retrieval_defaults=RetrievalDefaults(
            top_k=int(retrieval.get("top_k", 4)),
            min_similarity=float(retrieval.get("min_similarity", 0.2)),
        ),
        source_docs=[
            SourceDoc(
                doc_file=d["doc_file"],
                doc_title=d.get("doc_title", ""),
                doc_tag=d.get("doc_tag", "doc"),
                instructor_only=bool(d.get("instructor_only", False)),
            )
            for d in always_include + chunks
        ],
    )
    store.put_bytes(f"{vs_prefix}/index.faiss", build_faiss_bytes(vectors))
    put_json(store, f"{vs_prefix}/chunks.json", {"chunks": chunks, "always_include": always_include})
    put_json(store, f"{vs_prefix}/manifest.json", manifest.model_dump())

    # ---- prompt ----
    prompt_key = f"{prefix}/{agent_id}/prompts/system.md"
    if system_prompt_file is not None:
        store.put_text(prompt_key, Path(system_prompt_file).read_text(encoding="utf-8"))
    elif not store.exists(prompt_key):
        raise ValueError(
            f"No existe {prompt_key} y no se pasó --system-prompt-file — "
            f"el agente no puede operar sin prompt."
        )

    # ---- config.json (crear o actualizar) ----
    config_created = False
    try:
        config = read_agent_config(store, prefix, agent_id)
    except ObjectNotFoundError:
        config_created = True
        config = AgentConfigDoc(
            agent_id=agent_id,
            agent_name=agent_name or agent_id.title(),
            prompt_id="system-v1",
            prompt_s3_uri=f"s3://{store.bucket}/{prompt_key}",
            llm_model=llm_model,
            top_k=manifest.retrieval_defaults.top_k,
            min_similarity=manifest.retrieval_defaults.min_similarity,
            response_format="json",
            fallback_message=LEGACY_FALLBACK_MESSAGE,
            leak_markers=LEGACY_LEAK_MARKERS,
            leak_replacement_message=LEGACY_LEAK_REPLACEMENT,
            metadata={"migrated_from": str(Path(input_path).name), "case": legacy.get("name", "")},
        )
    if activate:
        config.vector_store_id = version
        config.vector_store_s3_uri = uri
        write_agent_config(store, prefix, agent_id, config)
    elif config_created:
        write_agent_config(store, prefix, agent_id, config)

    return MigrateResult(
        agent_id=agent_id,
        version=version,
        chunk_count=len(chunks),
        always_include_count=len(always_include),
        config_created=config_created,
        vector_store_s3_uri=uri,
    )
