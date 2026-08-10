# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

from pctx0.client import _Client


class Resource(_Client):
    _prefix: str

    def _require_workspace(self) -> str:
        if not self._workspace_id:
            raise ValueError("workspace_id is required")
        return self._workspace_id

    def _workspace_path(self, *parts: str) -> str:
        path = f"/api/v1/workspaces/{self._require_workspace()}"
        for part in parts:
            path = f"{path}/{part}"
        return path

    def _agent_path(self, agent_id: str, *parts: str) -> str:
        path = self._workspace_path("agents", agent_id)
        for part in parts:
            path = f"{path}/{part}"
        return path

    def __init__(
        self,
        *,
        base_url: str = "https://app.actx0.com",
        timeout: float = 30.0,
        access_key: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            access_key=access_key,
            workspace_id=workspace_id,
        )
