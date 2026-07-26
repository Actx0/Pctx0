# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from pctx0.resource.base import Resource
from pctx0.types import Agent, AgentList
from pctx0.utils import _DELETE, _GET, _POST, _PUT, build_query_params


class Agents(Resource):
    """Workspace agent API client."""

    _prefix = "/api/v1/agent"

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> AgentList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._workspace_path("agents"),
            params=params,
        )
        return AgentList.from_api(data)

    def get(self, agent_id: str) -> Agent:
        data = self._request(
            _GET,
            self._workspace_path("agents", agent_id),
        )
        return Agent.from_api(data)

    def create(
        self,
        *,
        name: str,
        description: str,
    ) -> Agent:
        data = self._request(
            _POST,
            self._workspace_path("agents"),
            json={"name": name, "description": description},
        )
        return Agent.from_api(data)

    def update(
        self,
        agent_id: str,
        *,
        name: str,
        description: str,
    ) -> Agent:
        data = self._request(
            _PUT,
            self._workspace_path("agents", agent_id),
            json={"name": name, "description": description},
        )
        return Agent.from_api(data)

    def delete(self, agent_id: str) -> None:
        self._request(
            _DELETE,
            self._workspace_path("agents", agent_id),
        )
