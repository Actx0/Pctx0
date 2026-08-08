#!/usr/bin/env python3
"""Create a prompt, add a version, fetch it by handle, then delete it.

uv run python examples/04_prompts.py
"""

from __future__ import annotations

from dataclasses import asdict
from pprint import pp

from pctx0 import Pctx0Client

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://actx0.com"


def main() -> None:
    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    created = client.prompt.create(
        name="Mara Guide",
        type="text",
        content="You answer questions about Mara Ellison using retrieved context.",
        description="System prompt for the Mara docs agent",
        commit_message="initial",
        production=True,
    )
    print("Created prompt")
    print("=" * 40)
    pp(asdict(created), sort_dicts=False, width=100)

    version = client.prompt.create_version(
        created.prompt_id,
        type="text",
        content=(
            "You answer questions about Mara Ellison using only the provided context. "
            "Cite sources like [1]. If the context is missing an answer, say so."
        ),
        commit_message="add citation rule",
        production=True,
    )
    print("\nCreated version")
    print("=" * 40)
    pp(asdict(version), sort_dicts=False, width=100)

    latest = client.prompt.get_by_name(created.handle)
    print("\nFetched by handle")
    print("=" * 40)
    pp(asdict(latest), sort_dicts=False, width=100)
    print(f"\ncompiled: {latest.compile()}")

    client.prompt.delete(created.prompt_id)
    print(f"\nDeleted {created.prompt_id}")

    client.close()


if __name__ == "__main__":
    main()
