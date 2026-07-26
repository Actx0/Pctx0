# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import json
from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import (
    Prompt,
    PromptInfo,
    PromptList,
    PromptStatus,
    PromptType,
    PromptVersionList,
)
from pctx0.utils import _DELETE, _GET, _POST, _PUT, build_query_params


def _encode_json_field(value: dict[str, Any] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _prompt_write_body(
    *,
    content: str,
    type: PromptType | None = None,
    config: dict[str, Any] | str | None = None,
    commit_message: str | None = None,
    meta: dict[str, Any] | str | None = None,
    status: PromptStatus | None = None,
    production: bool | None = None,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"content": content}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if type is not None:
        body["type"] = type
    encoded_config = _encode_json_field(config)
    if encoded_config is not None:
        body["config"] = encoded_config
    if commit_message is not None:
        body["commitMessage"] = commit_message
    encoded_meta = _encode_json_field(meta)
    if encoded_meta is not None:
        body["meta"] = encoded_meta
    if status is not None:
        body["status"] = status
    if production is not None:
        body["production"] = production
    return body


class Prompts(Resource):
    """Workspace prompt API client."""

    _prefix = "/api/v1/prompt"

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> PromptList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._workspace_path("prompts"),
            params=params,
        )
        return PromptList.from_api(data)

    def create(
        self,
        *,
        name: str,
        type: PromptType,
        content: str,
        description: str | None = None,
        config: dict[str, Any] | str | None = None,
        commit_message: str | None = None,
        meta: dict[str, Any] | str | None = None,
        production: bool | None = None,
    ) -> PromptInfo:
        body = _prompt_write_body(
            name=name,
            description=description,
            type=type,
            content=content,
            config=config,
            commit_message=commit_message,
            meta=meta,
            production=production,
        )
        data = self._request(
            _POST,
            self._workspace_path("prompts"),
            json=body,
        )
        return PromptInfo.from_api(data)

    def get(self, prompt_id: str) -> PromptInfo:
        data = self._request(
            _GET,
            self._workspace_path("prompts", prompt_id),
        )
        return PromptInfo.from_api(data)

    def delete(self, prompt_id: str) -> None:
        self._request(
            _DELETE,
            self._workspace_path("prompts", prompt_id),
        )

    def get_by_name(self, name: str, *, version: str | None = None) -> Prompt:
        params: dict[str, str] | None = None
        if version is not None:
            params = {"version": version}
        data = self._request(
            _GET,
            self._workspace_path("promptsByName", name),
            params=params,
        )
        return Prompt.from_api(data)

    def list_versions(
        self,
        prompt_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> PromptVersionList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._workspace_path("prompts", prompt_id, "versions"),
            params=params,
        )
        return PromptVersionList.from_api(data)

    def create_version(
        self,
        prompt_id: str,
        *,
        type: PromptType,
        content: str,
        config: dict[str, Any] | str | None = None,
        commit_message: str | None = None,
        meta: dict[str, Any] | str | None = None,
        production: bool | None = None,
    ) -> Prompt:
        body = _prompt_write_body(
            type=type,
            content=content,
            config=config,
            commit_message=commit_message,
            meta=meta,
            production=production,
        )
        data = self._request(
            _POST,
            self._workspace_path("prompts", prompt_id, "versions"),
            json=body,
        )
        return Prompt.from_api(data)

    def get_version(self, prompt_id: str, version_id: str) -> Prompt:
        data = self._request(
            _GET,
            self._workspace_path("prompts", prompt_id, "versions", version_id),
        )
        return Prompt.from_api(data)

    def update_version(
        self,
        prompt_id: str,
        version_id: str,
        *,
        content: str,
        type: PromptType | None = None,
        config: dict[str, Any] | str | None = None,
        commit_message: str | None = None,
        meta: dict[str, Any] | str | None = None,
        status: PromptStatus | None = None,
        production: bool | None = None,
    ) -> Prompt:
        body = _prompt_write_body(
            content=content,
            type=type,
            config=config,
            commit_message=commit_message,
            meta=meta,
            status=status,
            production=production,
        )
        data = self._request(
            _PUT,
            self._workspace_path("prompts", prompt_id, "versions", version_id),
            json=body,
        )
        return Prompt.from_api(data)

    def delete_version(self, prompt_id: str, version_id: str) -> None:
        self._request(
            _DELETE,
            self._workspace_path("prompts", prompt_id, "versions", version_id),
        )
