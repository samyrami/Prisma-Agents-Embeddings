"""Tests del pipeline de ingesta end-to-end (fake S3 + fake embeddings)."""

from __future__ import annotations

import json

import faiss
import numpy as np
import pytest

from tests.fakes import FakeEmbedder, FakeStore
from westfield_agent_ingest.pipeline import run_ingest
from westfield_agent_ingest.s3_io import ObjectNotFoundError
from westfield_agent_ingest.scaffold import scaffold_agent


def _setup_agent_with_docs(store: FakeStore, agent_id: str = "demo") -> None:
    scaffold_agent(store, agent_id, "Demo")
    store.put_text(f"agents/{agent_id}/docs/caso.md", "Contenido del caso académico. " * 20)
    store.put_text(f"agents/{agent_id}/docs/guia.md", "Guía operativa completa del agente.")
    store.put_text(
        f"agents/{agent_id}/docs/docs.json",
        json.dumps(
            {
                "docs": [
                    {"file": "caso.md", "title": "Caso académico", "tag": "case"},
                    {
                        "file": "guia.md",
                        "title": "Guía operativa",
                        "tag": "operating_guide",
                        "always_include": True,
                    },
                ]
            }
        ),
    )


def test_run_ingest_publica_version_y_activa() -> None:
    store = FakeStore()
    _setup_agent_with_docs(store)
    embedder = FakeEmbedder()

    result = run_ingest(store, embedder, "demo", chunk_size=200, overlap=20)

    assert result.version == "v1"
    assert result.activated is True
    assert result.chunk_count > 1
    assert result.always_include_count == 1

    vs = "agents/demo/vector_store/v1"
    assert store.exists(f"{vs}/index.faiss")
    assert store.exists(f"{vs}/chunks.json")
    assert store.exists(f"{vs}/manifest.json")

    # chunks.json: invariante chunks[i] ↔ fila i del faiss.
    chunks_file = json.loads(store.get_text(f"{vs}/chunks.json"))
    index = faiss.deserialize_index(
        np.frombuffer(store.get_bytes(f"{vs}/index.faiss"), dtype=np.uint8)
    )
    assert index.ntotal == len(chunks_file["chunks"]) == result.chunk_count
    assert chunks_file["always_include"][0]["doc_title"] == "Guía operativa"

    # manifest consistente con el embedder.
    manifest = json.loads(store.get_text(f"{vs}/manifest.json"))
    assert manifest["embedding_model"] == "fake-embeddings"
    assert manifest["embedding_dimensions"] == index.d == 4
    assert manifest["chunk_count"] == result.chunk_count

    # config.json activado.
    config = json.loads(store.get_text("agents/demo/config.json"))
    assert config["vector_store_id"] == "v1"
    assert config["vector_store_s3_uri"] == "s3://test-bucket/agents/demo/vector_store/v1/"


def test_segunda_corrida_publica_v2_sin_pisar_v1() -> None:
    store = FakeStore()
    _setup_agent_with_docs(store)

    run_ingest(store, FakeEmbedder(), "demo")
    v1_manifest = store.get_bytes("agents/demo/vector_store/v1/manifest.json")

    result = run_ingest(store, FakeEmbedder(), "demo")
    assert result.version == "v2"
    # v1 quedó intacta (inmutable).
    assert store.get_bytes("agents/demo/vector_store/v1/manifest.json") == v1_manifest

    config = json.loads(store.get_text("agents/demo/config.json"))
    assert config["vector_store_id"] == "v2"


def test_no_activate_publica_sin_tocar_config() -> None:
    store = FakeStore()
    _setup_agent_with_docs(store)
    run_ingest(store, FakeEmbedder(), "demo")  # activa v1

    result = run_ingest(store, FakeEmbedder(), "demo", activate=False)
    assert result.version == "v2"
    config = json.loads(store.get_text("agents/demo/config.json"))
    assert config["vector_store_id"] == "v1"  # sigue apuntando a v1


def test_version_existente_es_error() -> None:
    store = FakeStore()
    _setup_agent_with_docs(store)
    run_ingest(store, FakeEmbedder(), "demo", version="v1")

    with pytest.raises(ValueError, match="inmutables"):
        run_ingest(store, FakeEmbedder(), "demo", version="v1")


def test_sin_config_pide_scaffold_primero() -> None:
    store = FakeStore()
    store.put_text("agents/demo/docs/caso.md", "contenido")

    with pytest.raises(ObjectNotFoundError):
        run_ingest(store, FakeEmbedder(), "demo")


def test_sin_docs_es_error() -> None:
    store = FakeStore()
    scaffold_agent(store, "demo", "Demo")  # crea docs/.keep pero ningún doc real

    with pytest.raises(ValueError, match="docs procesables"):
        run_ingest(store, FakeEmbedder(), "demo")


def test_source_local_lee_carpeta(tmp_path) -> None:
    store = FakeStore()
    scaffold_agent(store, "demo", "Demo")
    (tmp_path / "caso.md").write_text("Contenido local del caso. " * 30, encoding="utf-8")

    result = run_ingest(store, FakeEmbedder(), "demo", source="local", docs_dir=tmp_path)
    assert result.version == "v1"
    assert result.chunk_count >= 1
