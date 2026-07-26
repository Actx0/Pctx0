#!/usr/bin/env python3
"""Shared helpers for pctx0 examples (setup, RAG, OpenRouter streaming)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from pctx0 import (
    Memory,
    MemorySearchHit,
    Message,
    MessageSearchHit,
    Pctx0Client,
    SearchHit,
)

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "http://127.0.0.1:8000"

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
DOC_LABELS = {"source": "docs", "team": "platform-team"}


@dataclass(frozen=True, slots=True)
class Setup:
    agent_id: str
    prompt_id: str
    system: str
    session_id: str
    session_external_id: str


def setup(
    client: Pctx0Client,
    *,
    agent_name: str,
    agent_description: str,
    prompt_name: str,
    prompt_content: str,
    session_external_id: str,
    session_title: str,
) -> Setup:
    """Create a prompt, agent, and session."""
    prompt_info = client.prompt.create(
        name=prompt_name,
        type="text",
        content=prompt_content,
        commit_message="initial",
        production=True,
    )
    system = client.prompt.get_by_name(prompt_info.handle).content
    agent = client.agent.create(name=agent_name, description=agent_description)
    session = client.session.create(
        agent.id,
        external_id=session_external_id,
        title=session_title,
    )
    return Setup(
        agent_id=agent.id,
        prompt_id=prompt_info.prompt_id,
        system=system,
        session_id=session.id,
        session_external_id=session_external_id,
    )


def teardown(client: Pctx0Client, setup: Setup) -> None:
    client.session.delete(setup.agent_id, external_id=setup.session_external_id)
    client.agent.delete(setup.agent_id)
    client.prompt.delete(setup.prompt_id)


def rag_context(client: Pctx0Client, query: str, *, limit: int = 3) -> str:
    results = client.document.search(query=query, labels=DOC_LABELS, limit=limit)
    return format_hits(results.results, limit=limit)


def history_from_messages(messages: list[Message]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def history_from_message_hits(hits: list[MessageSearchHit]) -> list[dict[str, str]]:
    return [{"role": hit.role, "content": hit.text} for hit in hits]


def history_from_memories(memories: list[Memory]) -> list[dict[str, str]]:
    if not memories:
        return []
    facts = "\n".join(f"- [{m.kind}] {m.content}" for m in memories)
    return [{"role": "assistant", "content": f"Here is what I remember:\n{facts}"}]


def history_from_memory_hits(hits: list[MemorySearchHit]) -> list[dict[str, str]]:
    if not hits:
        return []
    facts = "\n".join(f"- [{hit.kind}] {hit.text}" for hit in hits)
    return [{"role": "assistant", "content": f"Here is what I remember:\n{facts}"}]


def format_hits(hits: list[SearchHit], *, limit: int | None = None) -> str:
    selected = hits if limit is None else hits[:limit]
    if not selected:
        return ""
    return "\n\n".join(f"[{i}] {hit.text}" for i, hit in enumerate(selected, start=1))


def build_messages(
    *,
    system: str,
    user: str,
    context: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    if context:
        user = f"Context:\n{context}\n\nQuestion: {user}"
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user})
    return messages


def ask(
    *,
    system: str,
    user: str,
    history: list[dict[str, str]],
    context: str,
) -> tuple[str, dict[str, int] | None]:
    messages = build_messages(
        system=system,
        user=user,
        context=context or None,
        history=history,
    )
    print(
        f"[ctx] history={len(history)} (prior turns) "
        f"sending={len(messages)} (system + history + current user)"
    )

    reply, usage = stream_response(messages=messages)
    if usage:
        print(
            f"[tokens] prompt={usage.get('prompt_tokens', '?')} "
            f"completion={usage.get('completion_tokens', '?')} "
            f"total={usage.get('total_tokens', '?')}"
        )
    return reply, usage


def stream_response(
    messages: list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    api_key: str = OPENROUTER_KEY,
    timeout: float = 60.0,
) -> tuple[str, dict[str, int] | None]:
    parts: list[str] = []
    usage: dict[str, int] | None = None
    print("agent> ", end="", flush=True)

    with httpx.stream(
        "POST",
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/actx0/pctx0",
            "X-Title": "pctx0 examples",
        },
        json={
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        },
        timeout=timeout,
    ) as response:
        if response.status_code >= 400:
            detail = response.read().decode()
            raise httpx.HTTPStatusError(
                f"OpenRouter error {response.status_code}: {detail}",
                request=response.request,
                response=response,
            )

        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ").strip()
            if not data or data == "[DONE]":
                if data == "[DONE]":
                    break
                continue

            chunk = json.loads(data)
            if chunk.get("usage"):
                usage = chunk["usage"]
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta", {}).get("content")
            if delta:
                print(delta, end="", flush=True)
                parts.append(delta)

    print("\n")
    return "".join(parts), usage
