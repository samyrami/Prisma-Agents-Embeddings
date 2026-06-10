"""Fakes de la suite de ingesta — sin AWS ni red."""

from __future__ import annotations

from westfield_agent_ingest.s3_io import ObjectNotFoundError


class FakeStore:
    """ObjectStore en memoria."""

    def __init__(self, bucket: str = "test-bucket") -> None:
        self._bucket = bucket
        self.objects: dict[str, bytes] = {}

    @property
    def bucket(self) -> str:
        return self._bucket

    def get_bytes(self, key: str) -> bytes:
        if key not in self.objects:
            raise ObjectNotFoundError(key)
        return self.objects[key]

    def get_text(self, key: str) -> str:
        return self.get_bytes(key).decode("utf-8")

    def put_bytes(self, key: str, data: bytes) -> None:
        self.objects[key] = data

    def put_text(self, key: str, text: str) -> None:
        self.put_bytes(key, text.encode("utf-8"))

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self.objects if k.startswith(prefix))

    def exists(self, key: str) -> bool:
        return key in self.objects


class FakeEmbedder:
    """Embedder determinístico (dim 4) — registra los textos embebidos."""

    model = "fake-embeddings"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        # Vector unitario distinto por posición (rota entre 4 ejes).
        out = []
        for i, _ in enumerate(texts):
            vec = [0.0, 0.0, 0.0, 0.0]
            vec[i % 4] = 1.0
            out.append(vec)
        return out
