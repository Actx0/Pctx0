# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from pathlib import Path

import pytest

from pctx0 import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNKING_STRATEGY,
    TextChunk,
    chunk,
    chunk_file,
    chunk_text,
)


def test_default_chunk_constants() -> None:
    assert DEFAULT_CHUNKING_STRATEGY == "recursive"
    assert DEFAULT_CHUNK_SIZE == 2000
    assert DEFAULT_CHUNK_OVERLAP == 400


def test_chunk_text_empty() -> None:
    assert chunk_text("") == []


def test_chunk_text_short_stays_one() -> None:
    text = "hello actx0"
    parts = chunk_text(text)
    assert len(parts) == 1
    assert isinstance(parts[0], TextChunk)
    assert parts[0].text == text
    assert parts[0].index == 0


def test_chunk_text_splits_long_input() -> None:
    text = ("Section alpha. " * 200) + "\n\n" + ("Section beta. " * 200)
    parts = chunk_text(text)
    assert len(parts) > 1
    assert all(part.text for part in parts)
    assert [part.index for part in parts] == list(range(len(parts)))


def test_chunk_overlap_disabled() -> None:
    text = ("word " * 1200) + "\n\n" + ("other " * 1200)
    with_overlap = chunk_text(text, chunk_size=500, chunk_overlap=100)
    without = chunk_text(text, chunk_size=500, chunk_overlap=0)
    assert len(with_overlap) >= 1
    assert len(without) >= 1
    assert sum(len(p.text) for p in with_overlap) >= sum(len(p.text) for p in without)


def test_chunk_file_and_as_file(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("# Title\n\n" + ("body paragraph. " * 300), encoding="utf-8")

    parts = chunk_file(path, chunk_size=400, chunk_overlap=50)
    assert parts
    upload = parts[0].as_file(filename="note-0000.md", content_type="text/markdown")
    assert upload[0] == "note-0000.md"
    assert upload[2] == "text/markdown"
    assert upload[1].decode("utf-8") == parts[0].text


def test_chunk_dispatcher(tmp_path: Path) -> None:
    assert chunk("plain text only")[0].text == "plain text only"

    path = tmp_path / "doc.txt"
    path.write_text("from disk", encoding="utf-8")
    assert chunk(path)[0].text == "from disk"
    assert chunk(str(path))[0].text == "from disk"


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "match"),
    [
        (0, 0, "chunk_size"),
        (100, -1, "chunk_overlap"),
        (100, 100, "chunk_overlap must be < chunk_size"),
    ],
)
def test_chunk_text_validation(
    chunk_size: int,
    chunk_overlap: int,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        chunk_text("abc", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
