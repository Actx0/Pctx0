#!/usr/bin/env python3
"""Create, list, get, update, and delete an agent.

uv run python examples/04_agents.py
"""

from __future__ import annotations

from dataclasses import asdict
from pprint import pp

from pctx0 import Pctx0Client

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://app.actx0.com"


def main() -> None:
    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    created = client.agent.create(
        name="Mara assistant",
        description="Answers questions about Mara Ellison from the docs knowledge base.",
    )
    print("Created")
    print("=" * 40)
    pp(asdict(created), sort_dicts=False, width=100)

    listed = client.agent.list()
    print(f"\nListed (total={listed.total})")
    print("=" * 40)
    for agent in listed.agents:
        print(f"  {agent.id}  {agent.name}  status={agent.status}")

    fetched = client.agent.get(created.id)
    print("\nFetched")
    print("=" * 40)
    pp(asdict(fetched), sort_dicts=False, width=100)

    updated = client.agent.update(
        created.id,
        name="Mara assistant v2",
        description="Updated description for the Mara docs agent.",
    )
    print("\nUpdated")
    print("=" * 40)
    pp(asdict(updated), sort_dicts=False, width=100)

    client.agent.delete(created.id)
    print(f"\nDeleted {created.id}")

    client.close()


if __name__ == "__main__":
    main()
