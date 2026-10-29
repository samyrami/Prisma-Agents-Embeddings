"""
Contratos JSON compartidos con el runtime (Westfield_agent_back_python).

Duplicado CONSCIENTE: el contrato entre ambos repos es el JSON publicado en
S3, no el código Python. Si cambiás un shape acá, actualizá el modelo
espejo en el runtime (domain/agent.py, domain/rag.py) y ambos READMEs.

Archivos del contrato:
  agents/<agent_id>/config.json              → AgentConfigDoc
  agents/<agent_id>/docs/docs.json           → DocsSidecar (metadata opcional)
  agents/<agent_id>/vector_store/vN/
      manifest.json                          → VectorStoreManifest
      chunks.json                            → ChunksFile
      index.faiss                            → IndexFlatIP serializado

Invariante: chunks.json.chunks[i] ↔ fila i del index.faiss (vectores
L2-normalizados, métrica inner_product = coseno).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Niveles de razonamiento de los modelos de razonamiento (familia GPT-5.x).
# Espejo de domain/agent.py del runtime.
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"]

# Modelo con el que nacen los agentes nuevos (scaffold / migrate-legacy).
# gpt-4o-mini se retira de la API el 2027-01-14. gpt-5.6-luna es de
# razonamiento, así que va SIEMPRE con un reasoning_effort explícito.
DEFAULT_LLM_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT: ReasoningEffort = "none"


class HardRule(BaseModel):
    """
    Regla determinista que el RUNTIME aplica sobre la respuesta estructurada
    del agente (las reglas del prompt son sugerencias para el LLM; estas son
    garantías server-side).

    `when`: condiciones AND — key = path "state.<k>" o "structured.<k>",
            value = {operador: valor} (eq, ne, gt, gte, lt, lte, in, nin).
    `set`:  keys top-level a forzar en `structured` si todo `when` se cumple.
    """

    when: dict[str, dict[str, Any]] = Field(default_factory=dict)
    set: dict[str, Any] = Field(default_factory=dict)


class AgentConfigDoc(BaseModel):
    """Shape de agents/<agent_id>/config.json — fuente de verdad del agente."""

    agent_id: str
    agent_name: str
    prompt_id: str
    prompt_s3_uri: str
    vector_store_id: str | None = None
    vector_store_s3_uri: str | None = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.6
    max_tokens: int = 800
    # None = modelo clásico (gpt-4o). El default DEBE seguir siendo None: los
    # configs existentes no lo traen y el read-modify-write de la ingesta no
    # puede inventárselo — gpt-4o rechaza reasoning_effort.
    reasoning_effort: ReasoningEffort | None = None
    top_k: int = 4
    min_similarity: float = 0.2
    response_format: Literal["json", "text"] = "text"
    fallback_message: str | None = None
    leak_markers: list[str] = Field(default_factory=list)
    leak_replacement_message: str | None = None
    hard_rules: list[HardRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkMeta(BaseModel):
    """Un chunk indexado (el embedding vive en index.faiss, fila i)."""

    id: str
    doc_file: str
    doc_title: str
    doc_tag: str
    instructor_only: bool = False
    text: str


class AlwaysIncludeDoc(BaseModel):
    """Doc completo que el runtime inyecta verbatim cada turno (sin embedding)."""

    doc_file: str
    doc_title: str
    doc_tag: str
    instructor_only: bool = False
    text: str


class ChunksFile(BaseModel):
    """Shape de chunks.json."""

    chunks: list[ChunkMeta] = Field(default_factory=list)
    always_include: list[AlwaysIncludeDoc] = Field(default_factory=list)


class ChunkingParams(BaseModel):
    chunk_size_chars: int = 0
    chunk_overlap_chars: int = 0


class RetrievalDefaults(BaseModel):
    top_k: int = 4
    min_similarity: float = 0.2


class SourceDoc(BaseModel):
    doc_file: str
    doc_title: str = ""
    doc_tag: str = "doc"
    instructor_only: bool = False


class VectorStoreManifest(BaseModel):
    """Shape de manifest.json."""

    vector_store_id: str
    agent_id: str
    embedding_provider: str = "openai"
    embedding_model: str
    embedding_dimensions: int
    normalized: bool = True
    metric: str = "inner_product"
    generated_at: str = ""
    chunk_count: int = 0
    chunking: ChunkingParams = Field(default_factory=ChunkingParams)
    retrieval_defaults: RetrievalDefaults = Field(default_factory=RetrievalDefaults)
    source_docs: list[SourceDoc] = Field(default_factory=list)


class DocMeta(BaseModel):
    """Metadata de un doc fuente, declarada en el sidecar docs.json."""

    file: str
    title: str = ""
    tag: str = "doc"
    instructor_only: bool = False
    always_include: bool = False


class DocsSidecar(BaseModel):
    """Shape opcional de agents/<agent_id>/docs/docs.json."""

    docs: list[DocMeta] = Field(default_factory=list)
