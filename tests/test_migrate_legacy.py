"""Tests de la migración del índice legacy (sin re-embeber)."""

from __future__ import annotations

import json

import faiss
import numpy as np
import pytest

from tests.fakes import FakeStore
from westfield_agent_ingest.migrate_legacy import LEGACY_LEAK_MARKERS, migrate_legacy

LEGACY_INDEX = {
    "name": "etsy",
    "embedding_model": "text-embedding-3-small",
    "generated_at": "2026-06-04T23:20:09.568Z",
    "retrieval": {
        "top_k": 4,
        "min_similarity": 0.2,
        "chunk_size_chars": 1400,
        "chunk_overlap_chars": 200,
    },
    "always_include": [
        {
            "doc_file": "guia.docx",
            "doc_title": "Guía operativa",
            "doc_tag": "operating_guide",
            "instructor_only": False,
            "text": "texto de la guía",
        }
    ],
    "chunks": [
        {
            "id": "caso.pdf#0",
            "doc_file": "caso.pdf",
            "doc_title": "Caso",
            "doc_tag": "case",
            "instructor_only": False,
            "text": "fragmento uno",
            "embedding": [1.0, 0.0, 0.0, 0.0],
        },
        {
            "id": "caso.pdf#1",
            "doc_file": "caso.pdf",
            "doc_title": "Caso",
            "doc_tag": "case",
            "instructor_only": True,
            "text": "fragmento dos",
            "embedding": [0.0, 1.0, 0.0, 0.0],
        },
    ],
}


def _write_inputs(tmp_path):
    index_path = tmp_path / "maia-index.json"
    index_path.write_text(json.dumps(LEGACY_INDEX), encoding="utf-8")
    prompt_path = tmp_path / "maia-system.md"
    prompt_path.write_text("# Identidad\nSos Maia.", encoding="utf-8")
    return index_path, prompt_path


def test_migra_chunks_embeddings_y_config(tmp_path) -> None:
    store = FakeStore()
    index_path, prompt_path = _write_inputs(tmp_path)

    result = migrate_legacy(
        store, "maia", index_path, system_prompt_file=prompt_path, agent_name="Maia"
    )

    assert result.version == "v1"
    assert result.chunk_count == 2
    assert result.always_include_count == 1
    assert result.config_created is True

    vs = "agents/maia/vector_store/v1"
    # FAISS: embeddings legacy reutilizados tal cual (sin re-embeber).
    index = faiss.deserialize_index(
        np.frombuffer(store.get_bytes(f"{vs}/index.faiss"), dtype=np.uint8)
    )
    assert index.ntotal == 2
    assert index.d == 4
    _scores, ids = index.search(np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32), 1)
    assert ids[0][0] == 0  # el vector e1 matchea el chunk 0

    # chunks.json sin el campo embedding.
    chunks_file = json.loads(store.get_text(f"{vs}/chunks.json"))
    assert len(chunks_file["chunks"]) == 2
    assert "embedding" not in chunks_file["chunks"][0]
    assert chunks_file["chunks"][1]["instructor_only"] is True
    assert chunks_file["always_include"][0]["doc_tag"] == "operating_guide"

    # manifest hereda metadata legacy.
    manifest = json.loads(store.get_text(f"{vs}/manifest.json"))
    assert manifest["embedding_model"] == "text-embedding-3-small"
    assert manifest["retrieval_defaults"] == {"top_k": 4, "min_similarity": 0.2}
    assert manifest["chunking"]["chunk_size_chars"] == 1400

    # prompt publicado.
    assert store.get_text("agents/maia/prompts/system.md").startswith("# Identidad")

    # config.json creado con la mecánica de Maia.
    config = json.loads(store.get_text("agents/maia/config.json"))
    assert config["vector_store_id"] == "v1"
    assert config["response_format"] == "json"
    assert config["top_k"] == 4
    assert config["leak_markers"] == LEGACY_LEAK_MARKERS
    assert config["metadata"]["case"] == "etsy"


def test_migrar_sin_prompt_ni_archivo_es_error(tmp_path) -> None:
    store = FakeStore()
    index_path, _ = _write_inputs(tmp_path)

    with pytest.raises(ValueError, match="prompt"):
        migrate_legacy(store, "maia", index_path)


def test_migrar_preserva_config_existente(tmp_path) -> None:
    store = FakeStore()
    index_path, prompt_path = _write_inputs(tmp_path)
    migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)

    # Tunear el config a mano y re-migrar: solo cambia el puntero de versión.
    config = json.loads(store.get_text("agents/maia/config.json"))
    config["temperature"] = 0.9
    store.put_text("agents/maia/config.json", json.dumps(config))

    result = migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)
    assert result.version == "v2"
    assert result.config_created is False

    updated = json.loads(store.get_text("agents/maia/config.json"))
    assert updated["temperature"] == 0.9  # se preservó el tuneo
    assert updated["vector_store_id"] == "v2"


def test_remigrar_preserva_reasoning_effort(tmp_path) -> None:
    """El read-modify-write no puede borrar reasoning_effort (el agente quedaría en fallback)."""
    store = FakeStore()
    index_path, prompt_path = _write_inputs(tmp_path)
    migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)

    config = json.loads(store.get_text("agents/maia/config.json"))
    config.update(llm_model="gpt-5.6-terra", reasoning_effort="low", max_tokens=4000)
    store.put_text("agents/maia/config.json", json.dumps(config))

    migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)

    updated = json.loads(store.get_text("agents/maia/config.json"))
    assert updated["llm_model"] == "gpt-5.6-terra"
    assert updated["reasoning_effort"] == "low"
    assert updated["max_tokens"] == 4000


def test_remigrar_config_clasico_no_inventa_reasoning_effort(tmp_path) -> None:
    """Un config de gpt-4o sin el campo debe seguir en null: gpt-4o rechaza reasoning_effort."""
    store = FakeStore()
    index_path, prompt_path = _write_inputs(tmp_path)
    migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)

    config = json.loads(store.get_text("agents/maia/config.json"))
    config["llm_model"] = "gpt-4o"
    config.pop("reasoning_effort", None)
    store.put_text("agents/maia/config.json", json.dumps(config))

    migrate_legacy(store, "maia", index_path, system_prompt_file=prompt_path)

    updated = json.loads(store.get_text("agents/maia/config.json"))
    assert updated["llm_model"] == "gpt-4o"
    assert updated["reasoning_effort"] is None
