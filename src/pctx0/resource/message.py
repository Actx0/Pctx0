# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import (
    Message,
    MessageInput,
    MessageList,
    MessageRole,
    MessageSearchResults,
)
from pctx0.utils import (
    _DELETE,
    _GET,
    _POST,
    _PUT,
    build_message_batch_payload,
    build_query_params,
    encode_item,
    encode_update_body,
)


class Messages(Resource):
    """Session message API client."""

    _prefix = "/api/v1/message"

    def list(
        self,
        agent_id: str,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> MessageList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", session_id, "messages"),
            params=params,
        )
        return MessageList.from_api(data)

    def get(
        self,
        agent_id: str,
        session_id: str,
        message_id: str,
    ) -> Message:
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", session_id, "messages", message_id),
        )
        return Message.from_api(data)

    def search(
        self,
        agent_id: str,
        session_id: str,
        *,
        query: str,
        limit: int = 10,
    ) -> MessageSearchResults:
        data = self._request(
            _POST,
            self._agent_path(agent_id, "sessions", session_id, "messages", "search"),
            json={"query": query, "limit": limit},
        )
        return MessageSearchResults.from_api(data)

    def create(
        self,
        agent_id: str,
        session_id: str,
        message: MessageInput | list[MessageInput],
    ) -> Message | list[Message]:
        if isinstance(message, list):
            data = self._request(
                _POST,
                self._agent_path(agent_id, "sessions", session_id, "messages", "batch"),
                json=build_message_batch_payload(message),
            )
            return [Message.from_api(item) for item in data["messages"]]

        data = self._request(
            _POST,
            self._agent_path(agent_id, "sessions", session_id, "messages"),
            json=encode_item(message),
        )
        return Message.from_api(data)

    def update(
        self,
        agent_id: str,
        session_id: str,
        message_id: str,
        *,
        content: str,
        role: MessageRole | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Message:
        data = self._request(
            _PUT,
            self._agent_path(agent_id, "sessions", session_id, "messages", message_id),
            json=encode_update_body(content=content, meta=meta, role=role),
        )
        return Message.from_api(data)

    def delete(
        self,
        agent_id: str,
        session_id: str,
        id: str | list[str],
    ) -> None:
        if isinstance(id, list):
            self._request(
                _DELETE,
                self._agent_path(agent_id, "sessions", session_id, "messages", "batch"),
                json={"ids": id},
            )
        else:
            self._request(
                _DELETE,
                self._agent_path(agent_id, "sessions", session_id, "messages", id),
            )
