"""
Construcción del índice FAISS del contrato: IndexFlatIP serializado a bytes.

El runtime lo deserializa con faiss.deserialize_index(np.frombuffer(...)).
Vectores float32 L2-normalizados → inner product = similitud coseno.
"""

from __future__ import annotations

import faiss
import numpy as np


def build_faiss_bytes(vectors: list[list[float]]) -> bytes:
    """raises ValueError si no hay vectores o las dimensiones no coinciden."""
    if not vectors:
        raise ValueError("No hay vectores para indexar.")
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError("Los vectores no tienen dimensiones homogéneas.")
    index = faiss.IndexFlatIP(arr.shape[1])
    index.add(arr)
    return faiss.serialize_index(index).tobytes()
