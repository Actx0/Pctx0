# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import (
    Memory,
    MemoryInput,
    MemoryKind,
    MemoryList,
    MemorySearchResults,
)
from pctx0.utils import (
    _DELETE,
    _GET,
    _POST,
    _PUT,
    build_memory_batch_payload,
    build_query_params,
    encode_item,
    encode_update_body,
)


class Memories(Resource):
    """Session memory API client."""

    _prefix = "/api/v1/memory"

    def list(
        self,
        agent_id: str,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> MemoryList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", session_id, "memories"),
            params=params,
        )
        return MemoryList.from_api(data)

    def get(
        self,
        agent_id: str,
        session_id: str,
        memory_id: str,
    ) -> Memory:
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", session_id, "memories", memory_id),
        )
        return Memory.from_api(data)

    def search(
        self,
        agent_id: str,
        session_id: str,
        *,
        query: str,
        limit: int = 10,
    ) -> MemorySearchResults:
        data = self._request(
            _POST,
            self._agent_path(agent_id, "sessions", session_id, "memories", "search"),
            json={"query": query, "limit": limit},
        )
        return MemorySearchResults.from_api(data)

    def create(
        self,
        agent_id: str,
        session_id: str,
        memory: MemoryInput | list[MemoryInput],
    ) -> Memory | list[Memory]:
        if isinstance(memory, list):
            data = self._request(
                _POST,
                self._agent_path(agent_id, "sessions", session_id, "memories", "batch"),
                json=build_memory_batch_payload(memory),
            )
            return [Memory.from_api(item) for item in data["memories"]]

        data = self._request(
            _POST,
            self._agent_path(agent_id, "sessions", session_id, "memories"),
            json=encode_item(memory),
        )
        return Memory.from_api(data)

    def update(
        self,
        agent_id: str,
        session_id: str,
        memory_id: str,
        *,
        content: str,
        kind: MemoryKind | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Memory:
        data = self._request(
            _PUT,
            self._agent_path(agent_id, "sessions", session_id, "memories", memory_id),
            json=encode_update_body(content=content, meta=meta, kind=kind),
        )
        return Memory.from_api(data)

    def delete(
        self,
        agent_id: str,
        session_id: str,
        id: str | list[str],
    ) -> None:
        if isinstance(id, list):
            self._request(
                _DELETE,
                self._agent_path(agent_id, "sessions", session_id, "memories", "batch"),
                json={"ids": id},
            )
        else:
            self._request(
                _DELETE,
                self._agent_path(agent_id, "sessions", session_id, "memories", id),
            )
