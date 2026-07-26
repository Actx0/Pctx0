# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pctx0.types import (
    AccessKeyPrincipal,
    FileInput,
    MemoryInput,
    MessageInput,
)

_GET = "GET"
_POST = "POST"
_PUT = "PUT"
_DELETE = "DELETE"

_RESERVED_QUERY_KEYS = frozenset({"id", "limit", "offset"})


def build_query_params(
    *,
    external_id: str | None = None,
    labels: dict[str, str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if external_id is not None:
        params["id"] = external_id
    if labels:
        for key, value in labels.items():
            if key in _RESERVED_QUERY_KEYS:
                raise ValueError(f"reserved query key: {key}")
            params[key] = value
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return params


def stringify_meta(meta: dict[str, Any] | None) -> str | None:
    """Convert client-side metadata to the JSON string the API expects on write."""
    if meta is None:
        return None
    return json.dumps(meta)


def encode_item(item: MessageInput | MemoryInput) -> dict[str, str]:
    body = {key: value for key, value in item.items() if key != "meta"}
    meta = stringify_meta(item.get("meta"))
    if meta is not None:
        body["meta"] = meta
    return body


def build_message_batch_payload(
    items: list[MessageInput],
) -> dict[str, list[dict[str, str]]]:
    return {"messages": [encode_item(item) for item in items]}


def build_memory_batch_payload(
    items: list[MemoryInput],
) -> dict[str, list[dict[str, str]]]:
    return {"memories": [encode_item(item) for item in items]}


def encode_update_body(
    *,
    content: str,
    meta: dict[str, Any] | None = None,
    **fields: str | None,
) -> dict[str, str]:
    body = {key: value for key, value in fields.items() if value is not None}
    body["content"] = content
    encoded_meta = stringify_meta(meta)
    if encoded_meta is not None:
        body["meta"] = encoded_meta
    return body


def parse_me_principal(data: dict[str, Any]) -> AccessKeyPrincipal:
    principal_type = data["principalType"]
    if principal_type == "access_key":
        return AccessKeyPrincipal.from_api(data)
    raise ValueError(f"unknown principalType: {principal_type}")


def prepare_file(file: FileInput) -> tuple[str, bytes, str]:
    if isinstance(file, tuple):
        return file
    path = Path(file)
    content_type = "text/markdown" if path.suffix == ".md" else "text/plain"
    return path.name, path.read_bytes(), content_type
