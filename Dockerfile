# Imagen del servicio de ingesta — pensada para correr como job bajo demanda
# (no es un servicio always-on).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml ./
RUN poetry install --only main --no-root --no-interaction

# README.md es requerido por poetry para empaquetar el root (readme en pyproject).
COPY README.md ./
COPY src ./src
RUN poetry install --only main --no-interaction

ENTRYPOINT ["ingest"]
CMD ["--help"]
