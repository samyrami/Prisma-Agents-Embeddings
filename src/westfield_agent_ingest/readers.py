"""
Extracción de texto por tipo de archivo: .pdf (pypdf), .docx (python-docx),
.md/.txt (decode plano).

Los imports de pypdf/python-docx son lazy — solo se pagan si el agente
tiene docs de ese tipo.
"""

from __future__ import annotations

import io
from pathlib import PurePosixPath

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


def is_supported(filename: str) -> bool:
    return PurePosixPath(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def extract_text(filename: str, data: bytes) -> str:
    """
    Devuelve el texto plano del documento.

    raises ValueError si la extensión no está soportada.
    """
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(data)
    if suffix == ".docx":
        return _extract_docx(data)
    if suffix in {".md", ".txt"}:
        return data.decode("utf-8", errors="replace")
    raise ValueError(f"Extensión no soportada: {filename!r} (soportadas: {SUPPORTED_EXTENSIONS})")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip())


def _extract_docx(data: bytes) -> str:
    import docx

    document = docx.Document(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
