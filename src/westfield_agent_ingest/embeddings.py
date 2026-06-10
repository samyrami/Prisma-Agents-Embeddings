"""
Cliente de embeddings OpenAI para la ingesta (batch, sync).

Devuelve vectores L2-normalizados — MISMO criterio que el runtime, así el
inner product del IndexFlatIP equivale a similitud coseno. Si esto cambia,
cambia el contrato (manifest.normalized) y hay que tocar ambos repos.
"""

from __future__ import annotations

import time

import httpx
import numpy as np

DEFAULT_BASE_URL = "https://api.openai.com/v1"
BATCH_SIZE = 64
MAX_RETRIES = 3


class OpenAIEmbeddings:
    """Implementa el protocolo Embedder que consume pipeline.run_ingest."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY ausente — no se pueden generar embeddings.")
        self._api_key = api_key
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def embed_batch(self, texts: list[str], *, batch_size: int = BATCH_SIZE) -> list[list[float]]:
        """Embebe N textos en lotes, con reintentos + backoff. L2-normalizados."""
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            out.extend(self._embed_once(texts[i : i + batch_size]))
        return out

    def _embed_once(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                res = httpx.post(
                    f"{self._base_url}/embeddings",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_key}",
                    },
                    json={"model": self.model, "input": texts},
                    timeout=self._timeout,
                )
                if res.status_code >= 400:
                    raise RuntimeError(f"OpenAI embeddings {res.status_code}: {res.text[:300]}")
                data = res.json()
                items = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
                return [_l2_normalize(item["embedding"]) for item in items]
            except Exception as err:
                last_error = err
                if attempt < MAX_RETRIES:
                    time.sleep(2**attempt)  # backoff 2s, 4s
        raise RuntimeError(f"Embeddings fallaron tras {MAX_RETRIES} intentos: {last_error}")


def _l2_normalize(vector: list[float]) -> list[float]:
    arr = np.asarray(vector, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm == 0.0:
        return arr.tolist()
    return (arr / norm).tolist()
