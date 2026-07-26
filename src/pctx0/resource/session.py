# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import Session, SessionList
from pctx0.utils import _DELETE, _GET, _POST, _PUT, build_query_params


class Sessions(Resource):
    """Agent session API client."""

    _prefix = "/api/v1/session"

    def create(
        self,
        agent_id: str,
        *,
        external_id: str | None = None,
        labels: dict[str, str] | None = None,
        title: str | None = None,
    ) -> Session:
        params = build_query_params(external_id=external_id, labels=labels)
        if not params:
            raise ValueError("external_id or labels is required")

        body: dict[str, str] | None = None
        if title is not None:
            body = {"title": title}

        data = self._request(
            _POST,
            self._agent_path(agent_id, "sessions"),
            params=params,
            json=body,
        )
        return Session.from_api(data)

    def list(
        self,
        agent_id: str,
        *,
        external_id: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionList:
        params = build_query_params(
            external_id=external_id,
            labels=labels,
            limit=limit,
            offset=offset,
        )
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions"),
            params=params or None,
        )
        return SessionList.from_api(data)

    def get(
        self,
        agent_id: str,
        session_id: str,
    ) -> Session:
        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", session_id),
        )
        return Session.from_api(data)

    def get_by_labels(
        self,
        agent_id: str,
        *,
        external_id: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> Session:
        params = build_query_params(external_id=external_id, labels=labels)
        if not params:
            raise ValueError("external_id or labels is required")

        data = self._request(
            _GET,
            self._agent_path(agent_id, "sessions", "by-labels"),
            params=params,
        )
        return Session.from_api(data)

    def update(
        self,
        agent_id: str,
        *,
        external_id: str | None = None,
        labels: dict[str, str] | None = None,
        title: str | None = None,
        new_labels: dict[str, str] | None = None,
    ) -> Session:
        params = build_query_params(external_id=external_id, labels=labels)
        if not params:
            raise ValueError("external_id or labels is required")

        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if new_labels is not None:
            body["labels"] = new_labels

        data = self._request(
            _PUT,
            self._agent_path(agent_id, "sessions", "by-labels"),
            params=params,
            json=body,
        )
        return Session.from_api(data)

    def delete(
        self,
        agent_id: str,
        *,
        external_id: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> None:
        params = build_query_params(external_id=external_id, labels=labels)
        if not params:
            raise ValueError("external_id or labels is required")

        self._request(
            _DELETE,
            self._agent_path(agent_id, "sessions", "by-labels"),
            params=params,
        )
