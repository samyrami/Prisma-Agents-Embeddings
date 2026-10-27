"""
CLI del servicio de ingesta.

  ingest run            → docs → chunks → embeddings → FAISS → S3 (+ activar)
  ingest migrate-legacy → migra maia-index.json del backend mono-agente (sin re-embeber)
  ingest scaffold       → alta de un agente nuevo en S3 (sin tocar código)

Ver README para los contratos JSON que produce cada comando.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from westfield_agent_ingest.contracts import DEFAULT_LLM_MODEL, DEFAULT_REASONING_EFFORT
from westfield_agent_ingest.settings import load_settings

app = typer.Typer(help="Ingesta de bases vectoriales para el runtime multi-agente Westfield.")
console = Console()


def _effort_or_none(value: str) -> str | None:
    """`--reasoning-effort null` = modelo clásico (gpt-4o), que no acepta el parámetro."""
    return None if value.strip().lower() in ("", "null") else value


def _make_store():
    from westfield_agent_ingest.s3_io import S3Store

    settings = load_settings()
    return settings, S3Store(bucket=settings.s3_bucket, region=settings.aws_region)


@app.command()
def run(
    agent_id: str = typer.Option(..., "--agent-id", help="ID del agente (ej. maia)."),
    source: str = typer.Option("s3", "--source", help="Origen de los docs: s3 | local."),
    docs_dir: Path | None = typer.Option(
        None, "--docs-dir", help="Carpeta local de docs (requerida con --source local)."
    ),
    chunk_size: int = typer.Option(1000, "--chunk-size", help="Tamaño de chunk en chars."),
    overlap: int = typer.Option(100, "--overlap", help="Solape entre chunks en chars."),
    version: str | None = typer.Option(
        None, "--version", help="Versión destino (vN). Default: próxima libre."
    ),
    activate: bool = typer.Option(
        True, "--activate/--no-activate", help="Apuntar config.json a la versión nueva."
    ),
) -> None:
    """Construye y publica el vector store de un agente."""
    from westfield_agent_ingest.embeddings import OpenAIEmbeddings
    from westfield_agent_ingest.pipeline import run_ingest

    settings, store = _make_store()
    if not settings.openai_api_key:
        console.print("[red]ERROR: OPENAI_API_KEY ausente — la ingesta necesita embeddings.[/red]")
        raise typer.Exit(code=1)
    if source == "local" and docs_dir is None:
        console.print("[red]ERROR: --source local requiere --docs-dir.[/red]")
        raise typer.Exit(code=1)

    embedder = OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        base_url=settings.openai_base_url,
    )
    result = run_ingest(
        store,
        embedder,
        agent_id,
        prefix=settings.s3_prefix,
        source=source,
        docs_dir=docs_dir,
        chunk_size=chunk_size,
        overlap=overlap,
        version=version,
        activate=activate,
        embedding_provider=settings.embedding_provider,
    )
    console.print(
        f"[green]OK[/green] {result.agent_id} -> {result.vector_store_s3_uri} | "
        f"{result.chunk_count} chunks | {result.always_include_count} always_include | "
        f"{'ACTIVADA' if result.activated else 'sin activar'}"
    )


@app.command("migrate-legacy")
def migrate_legacy_cmd(
    agent_id: str = typer.Option(..., "--agent-id"),
    input_path: Path = typer.Option(..., "--input", help="Path al maia-index.json legacy."),
    system_prompt_file: Path | None = typer.Option(
        None, "--system-prompt-file", help="system.md a publicar como prompt del agente."
    ),
    agent_name: str | None = typer.Option(None, "--agent-name"),
    llm_model: str = typer.Option(DEFAULT_LLM_MODEL, "--model"),
    reasoning_effort: str = typer.Option(
        DEFAULT_REASONING_EFFORT,
        "--reasoning-effort",
        help="none | low | medium | high | xhigh | max; 'null' para modelos clásicos (gpt-4o).",
    ),
    activate: bool = typer.Option(True, "--activate/--no-activate"),
) -> None:
    """Migra un índice legacy (embeddings inline) al contrato nuevo, sin re-embeber."""
    from westfield_agent_ingest.migrate_legacy import migrate_legacy

    settings, store = _make_store()
    result = migrate_legacy(
        store,
        agent_id,
        input_path,
        prefix=settings.s3_prefix,
        system_prompt_file=system_prompt_file,
        agent_name=agent_name,
        llm_model=llm_model,
        reasoning_effort=_effort_or_none(reasoning_effort),
        activate=activate,
    )
    console.print(
        f"[green]OK[/green] {result.agent_id} migrado -> {result.vector_store_s3_uri} | "
        f"{result.chunk_count} chunks | {result.always_include_count} always_include | "
        f"config {'creado' if result.config_created else 'actualizado'}"
    )


@app.command()
def scaffold(
    agent_id: str = typer.Option(..., "--agent-id"),
    agent_name: str = typer.Option(..., "--agent-name"),
    llm_model: str = typer.Option(DEFAULT_LLM_MODEL, "--model"),
    reasoning_effort: str = typer.Option(
        DEFAULT_REASONING_EFFORT,
        "--reasoning-effort",
        help="none | low | medium | high | xhigh | max; 'null' para modelos clásicos (gpt-4o).",
    ),
    response_format: str = typer.Option("text", "--response-format", help="text | json"),
    system_prompt_file: Path | None = typer.Option(None, "--system-prompt-file"),
    force: bool = typer.Option(False, "--force", help="Pisar un agente existente."),
) -> None:
    """Da de alta un agente nuevo en S3 (config + prompt). Sin código, sin Docker."""
    from westfield_agent_ingest.scaffold import scaffold_agent

    settings, store = _make_store()
    result = scaffold_agent(
        store,
        agent_id,
        agent_name,
        prefix=settings.s3_prefix,
        llm_model=llm_model,
        reasoning_effort=_effort_or_none(reasoning_effort),
        response_format=response_format,
        system_prompt_file=system_prompt_file,
        force=force,
    )
    console.print(
        f"[green]OK[/green] Agente '{result.agent_id}' creado:\n"
        f"   config: s3://{store.bucket}/{result.config_key}\n"
        f"   prompt: s3://{store.bucket}/{result.prompt_key}\n"
        f"   Ya responde (sin RAG). Subí docs a {result.config_key.rsplit('/', 1)[0]}/docs/ "
        f"y corré `ingest run --agent-id {agent_id}` para darle RAG."
    )


if __name__ == "__main__":
    app()
