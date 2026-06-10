# Westfield Agent — Servicio de Ingesta (Python)

Servicio **independiente** del runtime conversacional (HU-001): su única
responsabilidad es **crear bases vectoriales** — parsea documentos, los
chunkea, genera embeddings (OpenAI, en batch) y publica el resultado en AWS S3
con el contrato que consume el runtime multi-agente
(repo hermano `Westfield_agent_back_python`).

El runtime **nunca** genera embeddings de documentos: solo embebe la query de
cada turno. Esta separación es un criterio de aceptación de la HU.

---

## Comandos

```bash
poetry install
cp .env.example .env           # OPENAI_API_KEY + credenciales AWS + S3_BUCKET

# 1) Alta de un agente nuevo (sin tocar código ni Docker):
poetry run ingest scaffold --agent-id soporte-ti --agent-name "Soporte TI" --model gpt-4o-mini

# 2) Construir y publicar su base vectorial (docs ya subidos a agents/<id>/docs/):
poetry run ingest run --agent-id soporte-ti --source s3
#    ... o desde una carpeta local:
poetry run ingest run --agent-id soporte-ti --source local --docs-dir ./mis-docs

# 3) Migrar el índice legacy de Maia (sin re-embeber):
poetry run ingest migrate-legacy --agent-id maia \
    --input ./legacy/maia-index.json \
    --system-prompt-file ./legacy/maia-system.md \
    --agent-name "Maia"

# Tests / lint
poetry run pytest -v
poetry run ruff check src tests
```

### `ingest run`

| Flag | Default | Notas |
|---|---|---|
| `--agent-id` | (requerido) | El agente debe existir (correr `scaffold` antes). |
| `--source` | `s3` | `s3` lee `agents/<id>/docs/`; `local` lee `--docs-dir`. |
| `--chunk-size` / `--overlap` | `1000` / `100` | Chars por chunk / solape. |
| `--version` | próxima libre | Las versiones son **inmutables** — nunca se pisan. |
| `--activate/--no-activate` | activate | Apunta `config.json` a la versión nueva. El runtime la recoge al expirar su TTL, sin reinicio. |

Tipos soportados: `.pdf` (pypdf), `.docx` (python-docx), `.md`, `.txt`.

### Metadata por documento (sidecar opcional)

`agents/<id>/docs/docs.json`:

```json
{
  "docs": [
    { "file": "caso.pdf", "title": "Caso académico", "tag": "case" },
    { "file": "notas.docx", "title": "Notas del instructor", "tag": "instructor_notes",
      "instructor_only": true },
    { "file": "guia.md", "title": "Guía operativa", "tag": "operating_guide",
      "always_include": true }
  ]
}
```

- `always_include: true` → el doc va ENTERO a `chunks.json.always_include`
  (el runtime lo inyecta verbatim cada turno; no se embebe).
- `instructor_only: true` → el runtime usa el contenido pero jamás expone su
  metadata en `sources`.
- Sin sidecar: `title` = nombre de archivo, `tag` = `doc`, todo público y chunkeable.

---

## Estructura que produce en S3

```
s3://westfield-agent-knowledge/
  agents/
    <agent_id>/
      config.json                  ← scaffold lo crea; run/migrate lo apuntan a la versión activa
      prompts/system.md            ← scaffold/migrate lo publican
      docs/                        ← fuentes (las sube el operador) + docs.json opcional
      vector_store/
        vN/
          index.faiss              ← faiss.IndexFlatIP serializado (float32, L2-normalizado)
          chunks.json              ← {"chunks": [...], "always_include": [...]}
          manifest.json            ← metadata + embedding_model/dimensions
```

## Contratos JSON (compartidos con el runtime)

> Espejo de los modelos en `src/westfield_agent_ingest/contracts.py`. Si cambiás
> un shape, actualizá también el runtime (`domain/agent.py`, `domain/rag.py`)
> y ambos READMEs. **El contrato es el JSON, no el código.**

### `config.json`

```json
{
  "agent_id": "maia",
  "agent_name": "Maia — Tutora Socrática Westfield",
  "prompt_id": "system-v1",
  "prompt_s3_uri": "s3://westfield-agent-knowledge/agents/maia/prompts/system.md",
  "vector_store_id": "v1",
  "vector_store_s3_uri": "s3://westfield-agent-knowledge/agents/maia/vector_store/v1/",
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "temperature": 0.6,
  "top_k": 4,
  "min_similarity": 0.2,
  "response_format": "json",
  "max_tokens": 800,
  "fallback_message": "...",
  "leak_markers": ["..."],
  "leak_replacement_message": "...",
  "hard_rules": [
    { "when": { "state.<key>": { "gte": 3 } }, "set": { "<flag>": true } }
  ],
  "metadata": {}
}
```

`hard_rules` (opcional): mecánicas deterministas que el runtime fuerza server-side
sobre la respuesta estructurada (`when` = condiciones AND sobre `state.*` /
`structured.*` con `eq, ne, gt, gte, lt, lte, in, nin`; `set` = keys a forzar).

### `manifest.json`

```json
{
  "vector_store_id": "v1",
  "agent_id": "maia",
  "embedding_provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "normalized": true,
  "metric": "inner_product",
  "generated_at": "2026-06-10T12:00:00Z",
  "chunk_count": 142,
  "chunking": { "chunk_size_chars": 1000, "chunk_overlap_chars": 100 },
  "retrieval_defaults": { "top_k": 4, "min_similarity": 0.2 },
  "source_docs": [ { "doc_file": "...", "doc_title": "...", "doc_tag": "...", "instructor_only": false } ]
}
```

### `chunks.json`

```json
{
  "chunks":         [ { "id", "doc_file", "doc_title", "doc_tag", "instructor_only", "text" } ],
  "always_include": [ { "doc_file", "doc_title", "doc_tag", "instructor_only", "text" } ]
}
```

**Invariante**: `chunks[i]` ↔ fila `i` del `index.faiss`. Vectores L2-normalizados,
métrica `inner_product` (= similitud coseno).

---

## Variables de entorno

| Var | Default | Notas |
|---|---|---|
| `S3_BUCKET` | `westfield-agent-knowledge` | Bucket destino. |
| `AWS_REGION` | `us-east-1` | |
| `S3_PREFIX` | `agents` | |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | — | Cadena estándar de boto3. Necesita permisos de **escritura**. |
| `OPENAI_API_KEY` | (requerido para `run`) | Embeddings de documentos. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Debe coincidir con lo que el runtime puede consumir. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | |

## Docker (opcional — para correrlo como job)

```bash
docker build -t westfield-ingest .
docker run --rm --env-file .env westfield-ingest run --agent-id maia --source s3
```

## Carpeta `legacy/`

- `maia-index.json` — índice del backend mono-agente original (embeddings inline).
- `maia-system.md` — prompt de Maia compuesto desde el `SYSTEM_PROMPT` legacy +
  reglas de avance + recordatorio final (insumo de `migrate-legacy`).
