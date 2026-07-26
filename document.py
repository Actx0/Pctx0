#!/usr/bin/env python3
"""Upload a text document and query its chunks.

uv run python document.py
"""

from __future__ import annotations

import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from pprint import pp

from pctx0 import Pctx0Client
from pctx0.types import Document

POLL_INTERVAL_S = 2
POLL_TIMEOUT_S = 120
_FAILED_STATUSES = frozenset({"failed", "error"})

# --- edit these ---
API_KEY = "7c24973a-e885-49f1-bafe-60ee93edd4ad"
ACCESS_KEY = "958403ea-9c2a-4754-b8a6-8c9cc346eb82"
WORKSPACE_ID = "bc61599d-cfc1-4a2c-b642-22e1004eb6f9"
BASE_URL = "http://127.0.0.1:8000"

DOC_PATH = Path("/Users/ahmedfathy/space/personal/actx0/testdata/life_of_samuel.txt")


def wait_until_indexed(client: Pctx0Client, document_id: str) -> Document:
    """Poll until the document finishes chunking and indexing."""
    deadline = time.monotonic() + POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        listed = client.document.list()
        doc = next((d for d in listed.documents if d.id == document_id), None)
        if doc is None:
            raise RuntimeError(f"document {document_id} not found")

        if doc.status in _FAILED_STATUSES:
            raise RuntimeError(f"indexing failed with status {doc.status!r}")
        if doc.status != "processing":
            return doc

        print(f"waiting for indexing... status={doc.status}")
        time.sleep(POLL_INTERVAL_S)

    raise TimeoutError(
        f"document {document_id} still processing after {POLL_TIMEOUT_S}s"
    )


def show(label: str, value: object) -> None:
    print(f"\n{'=' * 60}")
    print(label.title())
    print("=" * 60)
    if is_dataclass(value):
        pp(asdict(value), sort_dicts=False, width=100)
    else:
        print(value)


def main() -> None:
    with Pctx0Client(
        api_key=API_KEY,
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    ) as client:
        # Upload requires the user API key (not the access key).
        uploaded = client.document.upload(
            file=DOC_PATH,
            title="Life of Samuel Hawthorne",
            labels={"team": "support", "category": "biography"},
            auth="api_key",
        )
        show("uploaded document", uploaded)

        indexed = wait_until_indexed(client, uploaded.id)
        show("indexed document", indexed)

        queries = [
            "When and where was Samuel Hawthorne born?",
            "What did Samuel think about time and memory?",
            "How did Samuel spend his winters?",
        ]
        for query in queries:
            results = client.document.search(
                query=query,
                labels={"team": "support"},
                limit=3,
            )
            show(f'search: "{query}"', results)

        client.document.delete(uploaded.id, auth="api_key")


if __name__ == "__main__":
    main()
