"""Tests del chunking por caracteres con overlap."""

from __future__ import annotations

import pytest

from westfield_agent_ingest.chunking import chunk_text, normalize_text


def test_texto_corto_un_solo_chunk() -> None:
    assert chunk_text("hola mundo", size=100, overlap=10) == ["hola mundo"]


def test_texto_vacio_sin_chunks() -> None:
    assert chunk_text("", size=100, overlap=10) == []
    assert chunk_text("   \n\n  ", size=100, overlap=10) == []


def test_texto_largo_se_parte_con_overlap() -> None:
    words = " ".join(f"palabra{i}" for i in range(200))
    chunks = chunk_text(words, size=300, overlap=50)

    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    # El overlap hace que el final de un chunk reaparezca al inicio del siguiente.
    tail = chunks[0][-30:]
    assert tail.split()[-1] in chunks[1]


def test_no_parte_palabras_al_medio() -> None:
    words = " ".join(["supercalifragilistico"] * 100)
    chunks = chunk_text(words, size=100, overlap=10)
    for chunk in chunks:
        for word in chunk.split():
            assert word == "supercalifragilistico"


def test_overlap_mayor_o_igual_a_size_es_error() -> None:
    with pytest.raises(ValueError):
        chunk_text("x", size=100, overlap=100)


def test_normalize_text_colapsa_whitespace_y_preserva_parrafos() -> None:
    raw = "hola   mundo\t\tbien\n\n\n  segundo    párrafo  "
    assert normalize_text(raw) == "hola mundo bien\n\nsegundo párrafo"
