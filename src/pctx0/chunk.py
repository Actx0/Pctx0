# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

"""Document chunking helpers powered by chonkie.

Defaults match Actx0 knowledge-base settings: recursive strategy, size 2000,
overlap 400 (character tokens).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pctx0.types import FileInput
from pctx0.utils import prepare_file

if TYPE_CHECKING:
    from chonkie import OverlapRefinery, RecursiveChunker

DEFAULT_CHUNKING_STRATEGY = "recursive"
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 400
DEFAULT_TOKENIZER = "character"

_MISSING_CHONKIE = (
    "chunking requires the optional dependency 'chonkie'. "
    "Install with: uv add 'pctx0[chunk]'"
)


def _require_chonkie() -> tuple[Any, Any]:
    try:
        from chonkie import OverlapRefinery, RecursiveChunker
    except ImportError as exc:
        raise ImportError(_MISSING_CHONKIE) from exc
    return OverlapRefinery, RecursiveChunker


@dataclass(frozen=True, slots=True)
class TextChunk:
    """A text segment ready to upload or send to Actx0."""

    text: str
    index: int
    start_index: int
    end_index: int
    token_count: int

    def as_file(
        self,
        *,
        filename: str | None = None,
        content_type: str = "text/plain",
    ) -> tuple[str, bytes, str]:
        """Return an upload-ready ``(filename, bytes, content_type)`` tuple."""
        name = filename or f"chunk-{self.index:04d}.txt"
        return name, self.text.encode("utf-8"), content_type


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer: str = DEFAULT_TOKENIZER,
) -> list[TextChunk]:
    """Split ``text`` with Actx0-friendly recursive chunking defaults."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be < chunk_size")

    if not text:
        return []

    OverlapRefinery, RecursiveChunker = _require_chonkie()
    chunker = RecursiveChunker(tokenizer=tokenizer, chunk_size=chunk_size)
    raw = chunker.chunk(text)

    if chunk_overlap > 0 and len(raw) > 1:
        refinery = OverlapRefinery(
            tokenizer=tokenizer,
            context_size=chunk_overlap,
            method="prefix",
            merge=True,
            inplace=False,
        )
        raw = refinery.refine(raw)

    return [
        TextChunk(
            text=item.text,
            index=index,
            start_index=item.start_index,
            end_index=item.end_index,
            token_count=item.token_count,
        )
        for index, item in enumerate(raw)
    ]


def chunk_file(
    file: FileInput,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer: str = DEFAULT_TOKENIZER,
    encoding: str = "utf-8",
) -> list[TextChunk]:
    """Read a text/markdown file (or upload tuple) and chunk its contents."""
    _filename, content, _content_type = prepare_file(file)
    text = content.decode(encoding)
    return chunk_text(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        tokenizer=tokenizer,
    )


def chunk(
    source: str | Path | FileInput,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    tokenizer: str = DEFAULT_TOKENIZER,
    encoding: str = "utf-8",
) -> list[TextChunk]:
    """Chunk a string, path, or upload tuple using Actx0 defaults.

    Strings that are not existing paths are treated as raw text. Paths and
    upload tuples are loaded via :func:`chunk_file`.
    """
    if isinstance(source, tuple):
        return chunk_file(
            source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
            encoding=encoding,
        )

    if isinstance(source, Path):
        return chunk_file(
            source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
            encoding=encoding,
        )

    path = Path(source)
    if path.is_file():
        return chunk_file(
            path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokenizer=tokenizer,
            encoding=encoding,
        )

    return chunk_text(
        source,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        tokenizer=tokenizer,
    )
