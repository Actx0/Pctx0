#!/usr/bin/env python3
"""Upload docs, search them, then delete the uploaded documents.

uv run python examples/02_docs.py
"""

from __future__ import annotations

import time
from pathlib import Path

from pctx0 import Pctx0Client

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://actx0.com"

DOCS_DIR = Path(__file__).resolve().parent / "docs"
LABELS = {"tag": "docs", "team": "platform-team"}

QUERIES = [
    "Where does Mara live?",
    "What kind of work does Mara do?",
    "Who is in Mara's family?",
    "What are Mara's hobbies?",
]


def main() -> None:
    local_files = sorted(DOCS_DIR.glob("*.txt"))
    if not local_files:
        raise SystemExit(f"no .txt files in {DOCS_DIR}")

    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    listed = client.document.list(limit=100)
    print(f"remote documents ({listed.total}):")
    for doc in listed.documents:
        print(f"  {doc.filename} checksum={doc.checksum} status={doc.status}")

    doc_ids: list[str] = []
    print(f"\nlocal files ({len(local_files)}):")
    for path in local_files:
        existing = client.document.exists(file=path, labels=LABELS)
        if existing is not None:
            print(f"  skip  {path.name} (already uploaded {existing.id})")
            doc_ids.append(existing.id)
            continue

        uploaded = client.document.upload(
            file=path,
            title=path.stem.replace("_", " ").title(),
            labels=LABELS,
        )
        print(f"  upload {path.name} -> {uploaded.id} checksum={uploaded.checksum}")
        doc_ids.append(uploaded.id)

    print(f"\nwaiting {120} seconds for indexing...")
    time.sleep(120)

    print("\nsearch")
    print("=" * 40)
    for query in QUERIES:
        results = client.document.search(
            query=query,
            labels=LABELS,
            limit=3,
        )
        print(f"\nquery: {query}")
        print("-" * 40)
        if not results.results:
            print("  (no hits)")
            continue
        for hit in results.results:
            print(f"  [{hit.score:.2f}] {hit.text}")

    print("\ndelete")
    print("=" * 40)
    for doc_id in doc_ids:
        client.document.delete(doc_id)
        print(f"  deleted {doc_id}")

    client.close()


if __name__ == "__main__":
    main()
