#!/usr/bin/env python3
"""pctx0 playground — edit the calls in main() and run:

uv run python example.py
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pprint import pp

from pctx0 import Pctx0Client

# --- edit these ---
API_KEY = "7c24973a-e885-49f1-bafe-60ee93edd4ad"
ACCESS_KEY = "958403ea-9c2a-4754-b8a6-8c9cc346eb82"
WORKSPACE_ID = "bc61599d-cfc1-4a2c-b642-22e1004eb6f9"
BASE_URL = "http://127.0.0.1:8000"

AGENT_ID = ""  # leave empty to create one below
SESSION_ID = ""  # leave empty to create one below
PROMPT_HANDLE = "customer-support"


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
        # me
        show("me (api key)", client.me.get(auth="api_key"))
        show("me (access key)", client.me.get())

        # prompt
        prompt = client.prompt.get(handle=PROMPT_HANDLE)
        show("prompt", prompt)
        show("prompt compiled", prompt.compile(ctx="Ahmed"))

        # agents
        show("agents", client.agent.list())

        agent_id = AGENT_ID
        if not agent_id:
            agent = client.agent.create(
                name="Example bot", description="test", auth="api_key"
            )
            show("create agent", agent)
            agent_id = agent.id

        show("get agent", client.agent.get(agent_id))

        agent = client.agent.update(
            agent_id, name="Renamed bot", description="updated", auth="api_key"
        )
        show("update agent", agent)

        # session (required for messages + memories)
        session_id = SESSION_ID
        if not session_id:
            session = client.session.create(
                agent_id,
                external_id="example-thread",
                title="Example chat",
            )
            show("create session", session)
            session_id = session.id

        # messages
        message = client.message.create(
            agent_id,
            session_id,
            {
                "role": "user",
                "content": "Hello",
                "meta": {"source": "example", "confidence": 0.9},
            },
            auth="api_key",
        )
        show("create message", message)

        show(
            "list messages",
            client.message.list(agent_id, session_id),
        )
        show(
            "get message",
            client.message.get(agent_id, session_id, message.id),
        )

        message = client.message.update(
            agent_id,
            session_id,
            message.id,
            content="Updated",
            role="assistant",
            meta={"source": "example", "edited": True},
            auth="api_key",
        )
        show("update message", message)

        # client.message.delete(agent_id, session_id, message.id)
        show("delete message", "ok")

        # memories
        memory = client.memory.create(
            agent_id,
            session_id,
            {
                "kind": "fact",
                "content": "User is in Cairo",
                "meta": {"confidence": 0.9},
            },
            auth="api_key",
        )
        show("create memory", memory)

        show("list memories", client.memory.list(agent_id, session_id))
        show(
            "get memory",
            client.memory.get(agent_id, session_id, memory.id),
        )

        memory = client.memory.update(
            agent_id,
            session_id,
            memory.id,
            content="User is in Cairo, Egypt",
            meta={"confidence": 0.95, "verified": True},
            auth="api_key",
        )
        show("update memory", memory)

        # client.memory.delete(agent_id, session_id, memory.id)
        show("delete memory", "ok")

        # cleanup
        if not AGENT_ID:
            # client.agent.delete(agent_id)
            show("delete agent", "ok")


if __name__ == "__main__":
    main()
