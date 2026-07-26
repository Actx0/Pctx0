# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import hashlib
import json
from typing import Any

from pctx0.resource.base import Resource
from pctx0.types import Document, DocumentList, FileInput, SearchResults
from pctx0.utils import _DELETE, _GET, _POST, _PUT, build_query_params, prepare_file


class Documents(Resource):
    """Workspace knowledge base (documents) API client."""

    _prefix = "/api/v1/documents"

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentList:
        params = build_query_params(limit=limit, offset=offset)
        data = self._request(
            _GET,
            self._workspace_path("documents"),
            params=params,
        )
        return DocumentList.from_api(data)

    def exists(
        self,
        *,
        file: FileInput,
        labels: dict[str, str] | None = None,
        page_size: int = 50,
    ) -> Document | None:
        filename, content, _content_type = prepare_file(file)
        checksum = hashlib.sha256(content).hexdigest()
        expected_labels = (
            {f"{key}={value}" for key, value in labels.items()} if labels else set()
        )

        offset = 0
        while True:
            listed = self.list(limit=page_size, offset=offset)
            for doc in listed.documents:
                if (
                    doc.filename == filename
                    and doc.checksum == checksum
                    and set(doc.labels) == expected_labels
                ):
                    return doc
            offset += page_size
            if offset >= listed.total:
                return None

    def upload(
        self,
        *,
        file: FileInput,
        title: str,
        labels: dict[str, str] | None = None,
    ) -> Document:
        upload_file = prepare_file(file)
        data: dict[str, str] = {"title": title}
        if labels is not None:
            data["labels"] = json.dumps(
                [f"{key}={value}" for key, value in labels.items()]
            )

        result = self._request(
            _POST,
            self._workspace_path("documents"),
            data=data,
            files={"file": upload_file},
        )
        return Document.from_api(result)

    def search(
        self,
        *,
        query: str,
        labels: dict[str, str] | None = None,
        limit: int = 10,
    ) -> SearchResults:
        body: dict[str, Any] = {"query": query, "limit": limit}
        if labels is not None:
            body["labels"] = labels

        data = self._request(
            _POST,
            self._workspace_path("documents", "search"),
            json=body,
        )
        return SearchResults.from_api(data)

    def delete(self, document_id: str) -> None:
        self._request(
            _DELETE,
            self._workspace_path("documents", document_id),
        )


# Backward-compatible alias
Knowledge = Documents
