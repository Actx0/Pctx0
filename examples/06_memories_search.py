#!/usr/bin/env python3
"""Interactive personal assistant using memory search hits as history (+ RAG).

uv run python examples/06_memories_search.py
"""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

from pctx0 import Pctx0Client

sys.path.insert(0, str(Path(__file__).resolve().parent))
u = import_module("00_utils")

SYSTEM = (
    "You are a helpful personal assistant. Use what you remember about the user "
    "and any provided context to answer. Cite context like [1]. If unsure, say so."
)


def main() -> None:
    client = Pctx0Client(
        access_key=u.ACCESS_KEY,
        workspace_id=u.WORKSPACE_ID,
        base_url=u.BASE_URL,
    )
    s = u.setup(
        client,
        agent_name="Personal assistant (memories search)",
        agent_description="Personal assistant using memory search history + RAG.",
        prompt_name="Personal Assistant Memories Search",
        prompt_content=SYSTEM,
        session_external_id="personal-assistant-memories-search",
        session_title="Personal assistant — memories search",
    )
    print(f"agent={s.agent_id} session={s.session_id}")
    print("chat — quit/exit to stop\n")

    try:
        while True:
            text = input("you> ").strip()
            if not text or text.lower() in {"quit", "exit"}:
                break

            hits = client.memory.search(s.agent_id, s.session_id, query=text, limit=5)
            reply, usage = u.ask(
                system=s.system,
                user=text,
                history=u.history_from_memory_hits(hits.results),
                context=u.rag_context(client, text),
            )
            if reply:
                client.message.create(
                    s.agent_id,
                    s.session_id,
                    [
                        {"role": "user", "content": text},
                        {
                            "role": "assistant",
                            "content": reply,
                            "meta": {"model": u.DEFAULT_MODEL, "usage": usage},
                        },
                    ],
                )
    finally:
        u.teardown(client, s)
        client.close()


if __name__ == "__main__":
    main()
