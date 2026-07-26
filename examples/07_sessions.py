#!/usr/bin/env python3
"""Create sessions keyed by external_id or by labels.

uv run python examples/07_sessions.py
"""

from __future__ import annotations

from dataclasses import asdict
from pprint import pp

from pctx0 import Pctx0Client

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "http://127.0.0.1:8000"


def show(label: str, value: object) -> None:
    print(f"\n{label}")
    print("=" * 40)
    pp(asdict(value), sort_dicts=False, width=100)


def main() -> None:
    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    agent = client.agent.create(
        name="Sessions demo bot",
        description="Used only to demonstrate session create/lookup.",
    )
    print(f"agent={agent.id}")

    # 1) Create + look up by external_id (your own thread / ticket id).
    by_external_id = client.session.create(
        agent.id,
        external_id="support-ticket-42",
        title="Support ticket #42",
    )
    show("Created with external_id", by_external_id)

    fetched = client.session.get_by_labels(
        agent.id,
        external_id="support-ticket-42",
    )
    show("Fetched by external_id", fetched)

    # 2) Create + look up by labels (arbitrary key/value filters).
    by_labels = client.session.create(
        agent.id,
        labels={"userId": "u-100", "channel": "web"},
        title="Web chat for user u-100",
    )
    show("Created with labels", by_labels)

    fetched = client.session.get_by_labels(
        agent.id,
        labels={"userId": "u-100", "channel": "web"},
    )
    show("Fetched by labels", fetched)

    listed = client.session.list(agent.id)
    print(f"\nListed (total={listed.total})")
    print("=" * 40)
    for session in listed.sessions:
        print(
            f"  {session.id}  title={session.title!r}  "
            f"external_id={session.external_id!r}  labels={session.labels}"
        )

    # Cleanup: delete by the same keys used to create.
    client.session.delete(agent.id, external_id="support-ticket-42")
    print("\nDeleted session with external_id=support-ticket-42")

    client.session.delete(agent.id, labels={"userId": "u-100", "channel": "web"})
    print("Deleted session with labels={userId=u-100, channel=web}")

    client.agent.delete(agent.id)
    print(f"Deleted agent {agent.id}")

    client.close()


if __name__ == "__main__":
    main()
