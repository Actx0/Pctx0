#!/usr/bin/env python3
"""Chunk a long local biography with Actx0 defaults, then upload a sample.

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
    chunk_file,
)

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://app.actx0.com"

DOC_PATH = Path(__file__).resolve().parent / "docs" / "chunking" / "mara_long_bio.txt"
LABELS = {"tag": "chunked-docs", "team": "platform-team"}
# Upload only a few chunks so the demo stays quick against the live API.
UPLOAD_LIMIT = 3


def main() -> None:
    if not DOC_PATH.is_file():
        raise SystemExit(f"missing document: {DOC_PATH}")

    document_chars = DOC_PATH.stat().st_size
    print("chunking defaults")
    print("=" * 40)
    print(f"  strategy: {DEFAULT_CHUNKING_STRATEGY}")
    print(f"  size:     {DEFAULT_CHUNK_SIZE}")
    print(f"  overlap:  {DEFAULT_CHUNK_OVERLAP}")
    print(f"  source:   {DOC_PATH.name} ({document_chars:,} bytes)")

    chunks = chunk_file(DOC_PATH)
    print(f"\nchunks ({len(chunks)})")
    print("=" * 40)
    for part in chunks[:10]:
        preview = " ".join(part.text.split())[:80]
        print(
            f"  [{part.index:04d}] tokens={part.token_count} "
            f"span={part.start_index}:{part.end_index}  {preview}..."
        )

    if len(chunks) > 10:
        print(f"  ... {len(chunks) - 10} more chunks")

    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    to_upload = chunks[:UPLOAD_LIMIT]
    print(f"\nupload sample ({len(to_upload)} of {len(chunks)})")
    print("=" * 40)
    doc_ids: list[str] = []
    for part in to_upload:
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
