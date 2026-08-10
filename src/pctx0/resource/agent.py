# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import Agent, AgentList
from pctx0.utils import _DELETE, _GET, _POST, _PUT, build_query_params


def _agent_write_body(
    *,
    name: str,
    description: str,
    memory_pipeline: bool | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name, "description": description}
    if memory_pipeline is not None:
        body["configs"] = {"memoryPipeline": memory_pipeline}
    return body


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
        memory_pipeline: bool | None = None,
    ) -> Agent:
        """Create an agent.

        Omit ``memory_pipeline`` to leave pipeline off (API default). Pass
        ``True``/``False`` to set ``configs.memoryPipeline`` explicitly.
        """
        data = self._request(
            _POST,
            self._workspace_path("agents"),
            json=_agent_write_body(
                name=name,
                description=description,
                memory_pipeline=memory_pipeline,
            ),
        )
        return Agent.from_api(data)

    def update(
        self,
        agent_id: str,
        *,
        name: str,
        description: str,
        memory_pipeline: bool | None = None,
    ) -> Agent:
        """Update an agent.

        Pass ``memory_pipeline`` to set ``configs.memoryPipeline``. Omit it to
        leave configs out of the request body.
        """
        data = self._request(
            _PUT,
            self._workspace_path("agents", agent_id),
            json=_agent_write_body(
                name=name,
                description=description,
                memory_pipeline=memory_pipeline,
            ),
        )
        return Agent.from_api(data)

    def delete(self, agent_id: str) -> None:
        self._request(
            _DELETE,
            self._workspace_path("agents", agent_id),
        )
