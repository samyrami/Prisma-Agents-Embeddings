"""Tests del alta de agentes (scaffold)."""

from __future__ import annotations

import json

import pytest

from tests.fakes import FakeStore
from westfield_agent_ingest.scaffold import scaffold_agent


def test_scaffold_crea_config_prompt_y_docs() -> None:
    store = FakeStore()
    result = scaffold_agent(store, "soporte-ti", "Soporte TI", llm_model="gpt-4o-mini")

    config = json.loads(store.get_text(result.config_key))
    assert config["agent_id"] == "soporte-ti"
    assert config["agent_name"] == "Soporte TI"
    assert config["vector_store_id"] is None  # sin RAG hasta correr ingest run
    assert config["prompt_s3_uri"] == "s3://test-bucket/agents/soporte-ti/prompts/system.md"

    prompt = store.get_text(result.prompt_key)
    assert "Soporte TI" in prompt
    assert store.exists("agents/soporte-ti/docs/.keep")


def test_scaffold_no_pisa_agente_existente() -> None:
    store = FakeStore()
    scaffold_agent(store, "demo", "Demo")

    with pytest.raises(ValueError, match="ya existe"):
        scaffold_agent(store, "demo", "Demo 2")

    scaffold_agent(store, "demo", "Demo 2", force=True)  # con force sí
    config = json.loads(store.get_text("agents/demo/config.json"))
    assert config["agent_name"] == "Demo 2"


def test_scaffold_con_prompt_propio(tmp_path) -> None:
    store = FakeStore()
    prompt_file = tmp_path / "mi-prompt.md"
    prompt_file.write_text("# Identidad propia", encoding="utf-8")

    result = scaffold_agent(store, "demo", "Demo", system_prompt_file=prompt_file)
    assert store.get_text(result.prompt_key) == "# Identidad propia"
