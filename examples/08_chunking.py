#!/usr/bin/env python3
"""Chunk local docs with Actx0 defaults, then upload each chunk.

Requires the optional chunk extra:

    uv sync --extra chunk
    uv run python examples/08_chunking.py
"""

from __future__ import annotations

from pathlib import Path

from pctx0 import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNKING_STRATEGY,
    Pctx0Client,
    chunk_text,
)

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://app.actx0.com"

DOCS_DIR = Path(__file__).resolve().parent / "docs"
LABELS = {"tag": "chunked-docs", "team": "platform-team"}


def main() -> None:
    local_files = sorted(DOCS_DIR.glob("*.txt"))
    if not local_files:
        raise SystemExit(f"no .txt files in {DOCS_DIR}")

    # Join the short sample files into one longer document so defaults split it.
    document = "\n\n".join(path.read_text(encoding="utf-8") for path in local_files)

    print("chunking defaults")
    print("=" * 40)
    print(f"  strategy: {DEFAULT_CHUNKING_STRATEGY}")
    print(f"  size:     {DEFAULT_CHUNK_SIZE}")
    print(f"  overlap:  {DEFAULT_CHUNK_OVERLAP}")
    print(f"  source:   {len(local_files)} files, {len(document)} chars")

    chunks = chunk_text(document)
    print(f"\nchunks ({len(chunks)})")
    print("=" * 40)
    for part in chunks:
        preview = " ".join(part.text.split())[:80]
        print(
            f"  [{part.index:04d}] tokens={part.token_count} "
            f"span={part.start_index}:{part.end_index}  {preview}..."
        )

    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    print("\nupload")
    print("=" * 40)
    doc_ids: list[str] = []
    for part in chunks:
        filename = f"mara-bio-{part.index:04d}.txt"
        uploaded = client.document.upload(
            file=part.as_file(filename=filename),
            title=f"Mara Bio Part {part.index + 1}",
            labels=LABELS,
        )
        print(f"  {filename} -> {uploaded.id} status={uploaded.status}")
        doc_ids.append(uploaded.id)

    print("\ndelete")
    print("=" * 40)
    for doc_id in doc_ids:
        client.document.delete(doc_id)
        print(f"  deleted {doc_id}")

    client.close()


if __name__ == "__main__":
    main()
