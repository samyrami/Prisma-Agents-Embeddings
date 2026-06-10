"""
Chunking de texto por caracteres con overlap.

Estrategia simple y determinística: ventanas de `size` chars con `overlap`
de solape, cortando preferentemente en un límite de palabra para no partir
términos al medio. Suficiente para docs académicos; si hiciera falta
chunking semántico (por headers, por párrafos), va acá.
"""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Colapsa whitespace repetido preservando saltos de párrafo simples."""
    paragraphs = [_WHITESPACE.sub(" ", p).strip() for p in text.split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def chunk_text(text: str, *, size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Parte `text` en chunks de hasta `size` chars con `overlap` de solape.

    raises ValueError si overlap >= size (loop infinito).
    """
    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) debe ser menor que size ({size})")

    clean = normalize_text(text)
    if not clean:
        return []
    if len(clean) <= size:
        return [clean]

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + size, len(clean))
        window = clean[start:end]

        # Si no es el último chunk, retroceder hasta el último espacio para
        # no partir una palabra (si hay alguno razonablemente cerca).
        if end < len(clean):
            last_space = window.rfind(" ")
            if last_space > size // 2:
                window = window[:last_space]
                end = start + last_space

        chunks.append(window.strip())
        if end >= len(clean):
            break

        # El próximo chunk arranca `overlap` chars antes del corte, pero
        # retrocediendo hasta un límite de palabra para no arrancar al medio
        # de una (si no hay espacio útil, se acepta el corte crudo).
        next_start = end - overlap
        space = clean.rfind(" ", 0, next_start + 1)
        if space > start:
            next_start = space + 1
        start = max(next_start, start + 1)

    return [c for c in chunks if c]
