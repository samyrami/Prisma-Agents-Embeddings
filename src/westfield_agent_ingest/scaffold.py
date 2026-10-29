"""
Alta de un agente nuevo en S3 — sin tocar código ni Docker (criterio HU-001).

Crea el esqueleto mínimo para que el runtime lo sirva de inmediato:
  agents/<id>/config.json        (vector_store en null → agente sin RAG)
  agents/<id>/prompts/system.md  (placeholder o archivo provisto)
  agents/<id>/docs/.keep

Después: subir docs a agents/<id>/docs/ y correr `ingest run` para darle RAG.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from westfield_agent_ingest.contracts import (
    DEFAULT_LLM_MODEL,
    DEFAULT_REASONING_EFFORT,
    AgentConfigDoc,
    ReasoningEffort,
)
from westfield_agent_ingest.s3_io import ObjectStore, write_agent_config

PLACEHOLDER_PROMPT = """\
# Identidad
Sos {agent_name}, un agente conversacional de Westfield Business School.

# Reglas
- Respondé siempre en español neutro, de forma clara y profesional.
- Usá el contexto inyectado en los bloques `# Contexto siempre presente` y
  `# Contexto recuperado por relevancia` como fuente de verdad.
- Si no tenés información suficiente, decilo honestamente.

(Este prompt es un placeholder generado por `ingest scaffold` — reemplazalo
subiendo el system.md real a este mismo path.)
"""


@dataclass
class ScaffoldResult:
    agent_id: str
    config_key: str
    prompt_key: str


def scaffold_agent(
    store: ObjectStore,
    agent_id: str,
    agent_name: str,
    *,
    prefix: str = "agents",
    llm_model: str = DEFAULT_LLM_MODEL,
    reasoning_effort: ReasoningEffort | None = DEFAULT_REASONING_EFFORT,
    response_format: str = "text",
    system_prompt_file: str | Path | None = None,
    force: bool = False,
) -> ScaffoldResult:
    """raises ValueError si el agente ya existe (salvo force=True)."""
    config_key = f"{prefix}/{agent_id}/config.json"
    prompt_key = f"{prefix}/{agent_id}/prompts/system.md"

    if store.exists(config_key) and not force:
        raise ValueError(f"El agente '{agent_id}' ya existe ({config_key}). Usá --force para pisar.")

    if system_prompt_file is not None:
        prompt = Path(system_prompt_file).read_text(encoding="utf-8")
    else:
        prompt = PLACEHOLDER_PROMPT.format(agent_name=agent_name)

    config = AgentConfigDoc(
        agent_id=agent_id,
        agent_name=agent_name,
        prompt_id="system-v1",
        prompt_s3_uri=f"s3://{store.bucket}/{prompt_key}",
        vector_store_id=None,
        vector_store_s3_uri=None,
        llm_model=llm_model,
        reasoning_effort=reasoning_effort,
        response_format=response_format,  # type: ignore[arg-type]
    )

    store.put_text(prompt_key, prompt)
    write_agent_config(store, prefix, agent_id, config)
    store.put_text(f"{prefix}/{agent_id}/docs/.keep", "")

    return ScaffoldResult(agent_id=agent_id, config_key=config_key, prompt_key=prompt_key)
