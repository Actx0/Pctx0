# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations
from typing import Any, TypeVar
import httpx

from pctx0.utils import _GET

T = TypeVar("T", bound="_Client")


class _Client:
    """Base client core."""

    def __init__(
        self,
        *,
        base_url: str = "https://app.actx0.com",
        timeout: float = 30.0,
        access_key: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._access_key = access_key
        self._workspace_id = workspace_id
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
        )

    def _attach(self, resource: type[T]) -> T:
        instance = resource.__new__(resource)
        instance._base_url = self._base_url
        instance._timeout = self._timeout
        instance._access_key = self._access_key
        instance._workspace_id = self._workspace_id
        instance._http = self._http
        return instance

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        if not self._access_key:
            raise ValueError("access_key is required")
        request_headers = {"X-Access-Key": self._access_key}
        if headers:
            request_headers.update(headers)

        response = self._http.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class Pctx0Client(_Client):
    """Python client for the Actx0 Platform."""

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

        from pctx0.resource import (
            Agents,
            Documents,
            Me,
            Memories,
            Messages,
            Prompts,
            Sessions,
        )

        self.agent = self._attach(Agents)
        self.document = self._attach(Documents)
        self.knowledge = self.document
        self.me = self._attach(Me)
        self.memory = self._attach(Memories)
        self.message = self._attach(Messages)
        self.prompt = self._attach(Prompts)
        self.session = self._attach(Sessions)

    def health(self) -> dict[str, Any]:
        return self._request(_GET, "/api/v1/_health")
