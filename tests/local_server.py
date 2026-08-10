# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import hashlib
import json
import re
import uuid
from cgi import FieldStorage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_WORKSPACE_ACCESS_KEY = "test-workspace-access-key"
DEFAULT_WORKSPACE_ID = "ws-test-1"
DEFAULT_AGENT_ID = "agt-test-1"
_TIMESTAMP = "2026-07-11T10:00:00Z"


def _default_agent(agent_id: str = DEFAULT_AGENT_ID) -> dict[str, Any]:
    return {
        "id": agent_id,
        "workspaceId": DEFAULT_WORKSPACE_ID,
        "name": "Support bot",
        "kind": "unmanaged",
        "promptId": None,
        "kbLabels": {},
        "handle": "a8k2m9x1",
        "description": "Handles customer questions",
        "status": "active",
        "configs": {"memoryPipeline": False},
        "createdAt": _TIMESTAMP,
        "updatedAt": _TIMESTAMP,
    }


_AGENT_PREFIX_RE = re.compile(r"^/api/v1/workspaces/([^/]+)/agents/([^/]+)(/.*)?$")


class _Handler(BaseHTTPRequestHandler):
    agents: dict[str, dict[str, Any]] = {}
    documents: dict[str, dict[str, Any]] = {}
    sessions: dict[str, dict[str, Any]] = {}
    messages: dict[str, list[dict[str, Any]]] = {}
    memories: dict[str, list[dict[str, Any]]] = {}
    prompts: dict[str, dict[str, Any]] = {}
    prompt_versions: dict[str, dict[str, dict[str, Any]]] = {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _workspace_authorized(self) -> bool:
        return self.headers.get("X-Access-Key") == DEFAULT_WORKSPACE_ACCESS_KEY

    def _session_auth_ok(self) -> bool:
        return self._workspace_authorized()

    def _read_auth_ok(self) -> bool:
        return self._workspace_authorized()

    def _write_auth_ok(self) -> bool:
        return self._workspace_authorized()

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _send_json(self, status: int, data: dict[str, Any] | None = None) -> None:
        body = b"" if data is None else json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _query_labels(self, query: dict[str, list[str]]) -> dict[str, str]:
        labels: dict[str, str] = {}
        for key, values in query.items():
            if key not in {"id", "limit", "offset"} and values:
                labels[key] = values[0]
        return labels

    def _find_session_by_labels(
        self, query: dict[str, list[str]]
    ) -> dict[str, Any] | None:
        external_id = query.get("id", [None])[0]
        labels = self._query_labels(query)
        for session in self.sessions.values():
            if external_id and session["externalId"] == external_id:
                return session
            if labels and session.get("labels") == labels:
                return session
        return None

    def _session_response(self, session: dict[str, Any]) -> dict[str, Any]:
        return dict(session)

    def _list_meta(
        self, items: list[Any], query: dict[str, list[str]]
    ) -> dict[str, int]:
        limit = int(query.get("limit", ["50"])[0])
        offset = int(query.get("offset", ["0"])[0])
        return {"limit": limit, "offset": offset, "total": len(items)}

    def _read_multipart(self) -> dict[str, Any]:
        environ = {
            "REQUEST_METHOD": self.command,
            "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        form = FieldStorage(fp=self.rfile, environ=environ, headers=self.headers)
        result: dict[str, Any] = {}
        for key in form.keys() or []:
            item = form[key]
            if item.filename:
                result[key] = {
                    "filename": item.filename,
                    "content": item.file.read() if item.file else b"",
                }
            else:
                result[key] = item.value
        return result

    def _agent_object(
        self,
        agent_id: str,
        name: str,
        description: str,
        *,
        memory_pipeline: bool = False,
    ) -> dict[str, Any]:
        return {
            "id": agent_id,
            "workspaceId": DEFAULT_WORKSPACE_ID,
            "name": name,
            "kind": "unmanaged",
            "promptId": None,
            "kbLabels": {},
            "handle": uuid.uuid4().hex[:8],
            "description": description,
            "status": "active",
            "configs": {"memoryPipeline": memory_pipeline},
            "createdAt": _TIMESTAMP,
            "updatedAt": _TIMESTAMP,
        }

    def _document_object(
        self,
        document_id: str,
        *,
        title: str,
        filename: str,
        labels: list[str] | None = None,
        status: str = "processing",
        content: bytes = b"",
    ) -> dict[str, Any]:
        return {
            "id": document_id,
            "workspaceId": DEFAULT_WORKSPACE_ID,
            "title": title,
            "filename": filename,
            "contentType": "text/markdown",
            "checksum": hashlib.sha256(content).hexdigest(),
            "size": {"value": len(content) or 100, "unit": "bytes"},
            "charCount": len(content.decode("utf-8", errors="ignore")) or 80,
            "labels": labels or [],
            "chunkingStrategy": "recursive",
            "chunkSize": 2000,
            "chunkOverlap": 400,
            "status": status,
            "createdAt": _TIMESTAMP,
            "updatedAt": _TIMESTAMP,
        }

    def _workspace_route(
        self, path: str, query: dict[str, list[str]]
    ) -> tuple[int, dict[str, Any] | None]:
        ws_prefix = f"/api/v1/workspaces/{DEFAULT_WORKSPACE_ID}"

        if path == f"{ws_prefix}/agents":
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                agents = list(self.agents.values())
                return 200, {
                    "agents": agents,
                    "_meta": self._list_meta(agents, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                agent_id = f"agt_{uuid.uuid4().hex[:8]}"
                configs = body.get("configs") or {}
                memory_pipeline = bool(configs.get("memoryPipeline", False))
                agent = self._agent_object(
                    agent_id,
                    body["name"],
                    body["description"],
                    memory_pipeline=memory_pipeline,
                )
                self.agents[agent_id] = agent
                return 201, agent

        prompt_result = self._prompt_route(path, query, ws_prefix)
        if prompt_result[0] != 404:
            return prompt_result

        if path == f"{ws_prefix}/documents":
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                documents = list(self.documents.values())
                return 200, {
                    "documents": documents,
                    "_meta": self._list_meta(documents, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                form = self._read_multipart()
                file_info = form.get("file", {})
                filename = file_info.get("filename", "upload.md")
                content = file_info.get("content", b"")
                title = form.get("title", "Untitled")
                labels_raw = form.get("labels")
                labels = json.loads(labels_raw) if labels_raw else []
                document_id = f"doc_{uuid.uuid4().hex[:8]}"
                document = self._document_object(
                    document_id,
                    title=title,
                    filename=filename,
                    labels=labels,
                    content=content,
                )
                self.documents[document_id] = document
                return 201, document

        if path == f"{ws_prefix}/documents/search":
            if not self._read_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            body = self._read_json()
            return 200, {
                "results": [
                    {
                        "documentId": "doc_search_1",
                        "chunkId": "chunk_1",
                        "score": 0.87,
                        "text": f"Result for: {body['query']}",
                        "labels": body.get("labels", {}),
                    }
                ]
            }

        doc_prefix = f"{ws_prefix}/documents/"
        if path.startswith(doc_prefix):
            document_id = path[len(doc_prefix) :]
            if document_id in self.documents and self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                self.documents.pop(document_id)
                return 204, None

        return 404, {"errorMessage": "not found"}

    def _agent_route(
        self, path: str, query: dict[str, list[str]]
    ) -> tuple[int, dict[str, Any] | None]:
        match = _AGENT_PREFIX_RE.match(path)
        if not match:
            return 404, {"errorMessage": "not found"}

        workspace_id, agent_id, suffix = match.groups()
        if workspace_id != DEFAULT_WORKSPACE_ID:
            return 404, {"errorMessage": "workspace not found"}

        suffix = suffix or ""

        if suffix == "":
            agent = self.agents.get(agent_id)
            if agent is None:
                return 404, {"errorMessage": "Agent not found."}
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                return 200, agent
            if self.command == "PUT":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                agent["name"] = body["name"]
                agent["description"] = body["description"]
                if "configs" in body:
                    configs = body.get("configs") or {}
                    agent["configs"] = {
                        "memoryPipeline": bool(configs.get("memoryPipeline", False))
                    }
                agent["updatedAt"] = _TIMESTAMP
                return 200, agent
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                self.agents.pop(agent_id, None)
                return 204, None

        if suffix == "/sessions":
            if self.command == "POST":
                if not self._session_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                external_id = query.get("id", [None])[0]
                labels = self._query_labels(query)
                if not external_id and not labels:
                    return 400, {"errorMessage": "id or labels required"}
                if external_id and self._find_session_by_labels({"id": [external_id]}):
                    return 409, {"errorMessage": "Session already exists."}
                body = self._read_json()
                session_id = f"ses_{uuid.uuid4().hex[:8]}"
                session = {
                    "id": session_id,
                    "externalId": external_id or str(uuid.uuid4()),
                    "workspaceId": workspace_id,
                    "agentId": agent_id,
                    "title": body.get("title", ""),
                    "status": "active",
                    "labels": labels,
                    "meta": {},
                    "createdAt": _TIMESTAMP,
                    "updatedAt": _TIMESTAMP,
                }
                self.sessions[session_id] = session
                self.messages[session_id] = []
                self.memories[session_id] = []
                return 201, self._session_response(session)

            if self.command == "GET":
                if not self._session_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                sessions = [
                    s for s in self.sessions.values() if s["agentId"] == agent_id
                ]
                external_id = query.get("id", [None])[0]
                labels = self._query_labels(query)
                if external_id:
                    sessions = [s for s in sessions if s["externalId"] == external_id]
                if labels:
                    sessions = [s for s in sessions if s.get("labels") == labels]
                return 200, {
                    "sessions": [self._session_response(s) for s in sessions],
                    "_meta": self._list_meta(sessions, query),
                }

        if suffix == "/sessions/by-labels":
            if not self._session_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            session = self._find_session_by_labels(query)
            if session is None:
                return 404, {"errorMessage": "Session not found."}
            if self.command == "GET":
                return 200, self._session_response(session)
            if self.command == "PUT":
                body = self._read_json()
                if "title" in body:
                    session["title"] = body["title"]
                if "labels" in body:
                    session["labels"] = body["labels"]
                session["updatedAt"] = _TIMESTAMP
                return 200, self._session_response(session)
            if self.command == "DELETE":
                self.sessions.pop(session["id"], None)
                self.messages.pop(session["id"], None)
                self.memories.pop(session["id"], None)
                return 204, None

        session_match = re.match(r"^/sessions/([^/]+)$", suffix)
        if session_match and self.command == "GET":
            if not self._session_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            session_id = session_match.group(1)
            session = self.sessions.get(session_id)
            if session is None:
                return 404, {"errorMessage": "Session not found."}
            return 200, self._session_response(session)

        message_batch_match = re.match(r"^/sessions/([^/]+)/messages/batch$", suffix)
        if message_batch_match:
            session_id = message_batch_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                created = []
                for item in body["messages"]:
                    message = {
                        "id": f"msg_{uuid.uuid4().hex[:8]}",
                        "sessionId": session_id,
                        "role": item["role"],
                        "content": item["content"],
                        "meta": json.loads(item["meta"]) if item.get("meta") else {},
                        "createdAt": _TIMESTAMP,
                    }
                    self.messages[session_id].append(message)
                    created.append(message)
                return 201, {"messages": created}
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                delete_ids = set(body["ids"])
                items = self.messages.get(session_id, [])
                self.messages[session_id] = [
                    m for m in items if m["id"] not in delete_ids
                ]
                return 204, None

        message_search_match = re.match(r"^/sessions/([^/]+)/messages/search$", suffix)
        if message_search_match and self.command == "POST":
            if not self._read_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            session_id = message_search_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            body = self._read_json()
            query_text = body.get("query")
            limit = body.get("limit", 10)
            if (
                not isinstance(query_text, str)
                or not query_text
                or not 1 <= limit <= 100
            ):
                return 400, {"errorMessage": "Invalid search request."}
            matches = [
                {
                    "id": item["id"],
                    "role": item["role"],
                    "score": 0.91,
                    "text": item["content"],
                }
                for item in self.messages.get(session_id, [])
                if query_text.lower() in item["content"].lower()
            ]
            return 200, {"results": matches[:limit]}

        message_match = re.match(r"^/sessions/([^/]+)/messages$", suffix)
        if message_match:
            session_id = message_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                items = self.messages.get(session_id, [])
                return 200, {
                    "messages": items,
                    "_meta": self._list_meta(items, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                message = {
                    "id": f"msg_{uuid.uuid4().hex[:8]}",
                    "sessionId": session_id,
                    "role": body["role"],
                    "content": body["content"],
                    "meta": json.loads(body["meta"]) if body.get("meta") else {},
                    "createdAt": _TIMESTAMP,
                }
                self.messages[session_id].append(message)
                return 201, message

        message_item_match = re.match(r"^/sessions/([^/]+)/messages/([^/]+)$", suffix)
        if message_item_match:
            session_id, message_id = message_item_match.groups()
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            items = self.messages.get(session_id, [])
            message = next((m for m in items if m["id"] == message_id), None)
            if message is None:
                return 404, {"errorMessage": "Message not found."}
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                return 200, message
            if self.command == "PUT":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                if "role" in body:
                    message["role"] = body["role"]
                message["content"] = body["content"]
                if "meta" in body:
                    message["meta"] = json.loads(body["meta"])
                return 200, message
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                self.messages[session_id] = [m for m in items if m["id"] != message_id]
                return 204, None

        memory_batch_match = re.match(r"^/sessions/([^/]+)/memories/batch$", suffix)
        if memory_batch_match:
            session_id = memory_batch_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                created = []
                for item in body["memories"]:
                    memory = {
                        "id": f"mem_{uuid.uuid4().hex[:8]}",
                        "sessionId": session_id,
                        "kind": item["kind"],
                        "content": item["content"],
                        "meta": json.loads(item["meta"]) if item.get("meta") else {},
                        "createdAt": _TIMESTAMP,
                        "updatedAt": _TIMESTAMP,
                    }
                    self.memories[session_id].append(memory)
                    created.append(memory)
                return 201, {"memories": created}
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                delete_ids = set(body["ids"])
                items = self.memories.get(session_id, [])
                self.memories[session_id] = [
                    m for m in items if m["id"] not in delete_ids
                ]
                return 204, None

        memory_search_match = re.match(r"^/sessions/([^/]+)/memories/search$", suffix)
        if memory_search_match and self.command == "POST":
            if not self._read_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            session_id = memory_search_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            body = self._read_json()
            query_text = body.get("query")
            limit = body.get("limit", 10)
            if (
                not isinstance(query_text, str)
                or not query_text
                or not 1 <= limit <= 100
            ):
                return 400, {"errorMessage": "Invalid search request."}
            matches = [
                {
                    "id": item["id"],
                    "kind": item["kind"],
                    "score": 0.88,
                    "text": item["content"],
                }
                for item in self.memories.get(session_id, [])
                if query_text.lower() in item["content"].lower()
            ]
            return 200, {"results": matches[:limit]}

        memory_match = re.match(r"^/sessions/([^/]+)/memories$", suffix)
        if memory_match:
            session_id = memory_match.group(1)
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                items = self.memories.get(session_id, [])
                return 200, {
                    "memories": items,
                    "_meta": self._list_meta(items, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                memory = {
                    "id": f"mem_{uuid.uuid4().hex[:8]}",
                    "sessionId": session_id,
                    "kind": body["kind"],
                    "content": body["content"],
                    "meta": json.loads(body["meta"]) if body.get("meta") else {},
                    "createdAt": _TIMESTAMP,
                    "updatedAt": _TIMESTAMP,
                }
                self.memories[session_id].append(memory)
                return 201, memory

        memory_item_match = re.match(r"^/sessions/([^/]+)/memories/([^/]+)$", suffix)
        if memory_item_match:
            session_id, memory_id = memory_item_match.groups()
            if session_id not in self.sessions:
                return 404, {"errorMessage": "Session not found."}
            items = self.memories.get(session_id, [])
            memory = next((m for m in items if m["id"] == memory_id), None)
            if memory is None:
                return 404, {"errorMessage": "Memory not found."}
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                return 200, memory
            if self.command == "PUT":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                if "kind" in body:
                    memory["kind"] = body["kind"]
                memory["content"] = body["content"]
                if "meta" in body:
                    memory["meta"] = json.loads(body["meta"])
                memory["updatedAt"] = _TIMESTAMP
                return 200, memory
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                self.memories[session_id] = [m for m in items if m["id"] != memory_id]
                return 204, None

        return 404, {"errorMessage": "not found"}

    def _route(self) -> tuple[int, dict[str, Any] | None]:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if self.command == "GET" and path == "/api/v1/_health":
            return 200, {"status": "ok"}

        if self.command == "GET" and path == "/api/v1/me":
            return self._me_response()

        prompt_prefix = f"/api/v1/workspaces/{DEFAULT_WORKSPACE_ID}/promptsByName/"
        if self.command == "GET" and path.startswith(prompt_prefix):
            if not self._workspace_authorized():
                return 401, {"errorMessage": "Invalid access key."}
            handle = path[len(prompt_prefix) :]
            version = query.get("version", [None])[0]
            found = self._find_prompt_version_by_name(handle, version)
            if found is None:
                return 404, {"errorMessage": "prompt not found"}
            return 200, found

        if path.startswith(f"/api/v1/workspaces/{DEFAULT_WORKSPACE_ID}/agents/"):
            return self._agent_route(path, query)

        if path.startswith(f"/api/v1/workspaces/{DEFAULT_WORKSPACE_ID}/"):
            result = self._workspace_route(path, query)
            if result[0] != 404:
                return result

        resource_paths = (
            "/api/v1/agent",
            "/api/v1/knowledge",
            "/api/v1/prompt",
            "/api/v1/session",
        )
        if self.command == "GET" and path in resource_paths:
            if not self._workspace_authorized():
                return 401, {"errorMessage": "Invalid access key."}
            return 200, {"resource": path.rsplit("/", 1)[-1]}

        return 404, {"error": "not found"}

    def _me_response(self) -> tuple[int, dict[str, Any]]:
        access_key = self.headers.get("X-Access-Key")

        if access_key:
            if access_key != DEFAULT_WORKSPACE_ACCESS_KEY:
                return 401, {"errorMessage": "Invalid access key."}
            return 200, {
                "principalType": "access_key",
                "accessKey": {
                    "id": "wkey_ghi789",
                    "workspaceId": DEFAULT_WORKSPACE_ID,
                    "name": "Agent runtime",
                    "permissions": [
                        "CAN_LIST_AGENTS",
                        "CAN_GET_AGENT",
                    ],
                    "expiresAt": "2026-08-01T00:00:00Z",
                    "createdAt": "2026-07-05T08:00:00Z",
                    "updatedAt": "2026-07-05T08:00:00Z",
                },
            }

        return 403, {"errorMessage": "X-Access-Key header is required."}

    def _prompt_summary(self, prompt_id: str) -> dict[str, Any]:
        prompt = self.prompts[prompt_id]
        versions = self.prompt_versions.get(prompt_id, {})
        return {
            "promptId": prompt["promptId"],
            "name": prompt["name"],
            "handle": prompt["handle"],
            "description": prompt.get("description", ""),
            "versionCount": len(versions),
        }

    def _prompt_version_object(
        self,
        *,
        prompt: dict[str, Any],
        version_id: str,
        version: int,
        type: str,
        content: str,
        config: dict[str, Any] | str | None = None,
        commit_message: str | None = None,
        meta: str | None = None,
        status: str = "active",
        production: bool = False,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        if isinstance(config, str):
            parsed_config = json.loads(config) if config else {}
        else:
            parsed_config = config or {}
        return {
            "id": version_id,
            "name": prompt["name"],
            "handle": prompt["handle"],
            "description": prompt.get("description", ""),
            "version": version,
            "type": type,
            "content": content,
            "config": parsed_config,
            "labels": labels or [],
            "commitMessage": commit_message,
            "commitHash": uuid.uuid4().hex[:12],
            "meta": meta,
            "status": status,
            "production": production,
            "createdAt": _TIMESTAMP,
            "updatedAt": _TIMESTAMP,
        }

    def _find_prompt_by_handle(self, handle: str) -> dict[str, Any] | None:
        for prompt in self.prompts.values():
            if prompt["handle"] == handle:
                return prompt
        return None

    def _find_prompt_version_by_name(
        self, handle: str, version: str | None
    ) -> dict[str, Any] | None:
        prompt = self._find_prompt_by_handle(handle)
        if prompt is None:
            return None
        versions = list(self.prompt_versions.get(prompt["promptId"], {}).values())
        if not versions:
            return None
        versions.sort(key=lambda item: item["version"])

        if version in (None, "latest"):
            return versions[-1]
        if version == "production":
            for item in versions:
                if item.get("production"):
                    return item
            return versions[0]
        if version.startswith("v") and version[1:].isdigit():
            number = int(version[1:])
        elif version.isdigit():
            number = int(version)
        else:
            return None
        for item in versions:
            if item["version"] == number:
                return item
        return None

    def _prompt_route(
        self, path: str, query: dict[str, list[str]], ws_prefix: str
    ) -> tuple[int, dict[str, Any] | None]:
        if path == f"{ws_prefix}/prompts":
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                prompts = [self._prompt_summary(pid) for pid in self.prompts]
                return 200, {
                    "prompts": prompts,
                    "_meta": self._list_meta(prompts, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                prompt_id = f"prm_{uuid.uuid4().hex[:8]}"
                handle = body["name"].lower().replace(" ", "-")
                prompt = {
                    "promptId": prompt_id,
                    "name": body["name"],
                    "handle": handle,
                    "description": body.get("description", ""),
                }
                version_id = f"prv_{uuid.uuid4().hex[:8]}"
                version = self._prompt_version_object(
                    prompt=prompt,
                    version_id=version_id,
                    version=1,
                    type=body["type"],
                    content=body["content"],
                    config=body.get("config"),
                    commit_message=body.get("commitMessage"),
                    meta=body.get("meta"),
                    production=bool(body.get("production", False)),
                    labels=["latest"],
                )
                self.prompts[prompt_id] = prompt
                self.prompt_versions[prompt_id] = {version_id: version}
                return 201, self._prompt_summary(prompt_id)

        prompt_prefix = f"{ws_prefix}/prompts/"
        if not path.startswith(prompt_prefix):
            return 404, {"errorMessage": "not found"}

        remainder = path[len(prompt_prefix) :]
        parts = remainder.split("/")
        prompt_id = parts[0]
        if prompt_id not in self.prompts:
            return 404, {"errorMessage": "prompt not found"}

        if len(parts) == 1:
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                return 200, self._prompt_summary(prompt_id)
            if self.command == "DELETE":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                self.prompts.pop(prompt_id, None)
                self.prompt_versions.pop(prompt_id, None)
                return 204, None
            return 405, {"errorMessage": "method not allowed"}

        if parts[1] != "versions":
            return 404, {"errorMessage": "not found"}

        versions = self.prompt_versions.setdefault(prompt_id, {})
        prompt = self.prompts[prompt_id]

        if len(parts) == 2:
            if self.command == "GET":
                if not self._read_auth_ok():
                    return 401, {"errorMessage": "Invalid access key."}
                items = list(versions.values())
                items.sort(key=lambda item: item["version"])
                return 200, {
                    "versions": items,
                    "_meta": self._list_meta(items, query),
                }
            if self.command == "POST":
                if not self._write_auth_ok():
                    return 403, {"errorMessage": "Write requires user API key."}
                body = self._read_json()
                next_version = (
                    max((v["version"] for v in versions.values()), default=0) + 1
                )
                version_id = f"prv_{uuid.uuid4().hex[:8]}"
                production = bool(body.get("production", False))
                if production:
                    for item in versions.values():
                        item["production"] = False
                for item in versions.values():
                    item["labels"] = [
                        label for label in item["labels"] if label != "latest"
                    ]
                version = self._prompt_version_object(
                    prompt=prompt,
                    version_id=version_id,
                    version=next_version,
                    type=body["type"],
                    content=body["content"],
                    config=body.get("config"),
                    commit_message=body.get("commitMessage"),
                    meta=body.get("meta"),
                    production=production,
                    labels=["latest"],
                )
                versions[version_id] = version
                return 201, version
            return 405, {"errorMessage": "method not allowed"}

        version_id = parts[2]
        if version_id not in versions:
            return 404, {"errorMessage": "version not found"}

        if self.command == "GET":
            if not self._read_auth_ok():
                return 401, {"errorMessage": "Invalid access key."}
            return 200, versions[version_id]
        if self.command == "PUT":
            if not self._write_auth_ok():
                return 403, {"errorMessage": "Write requires user API key."}
            body = self._read_json()
            current = versions[version_id]
            if "type" in body:
                current["type"] = body["type"]
            current["content"] = body["content"]
            if "config" in body:
                config = body["config"]
                current["config"] = (
                    json.loads(config) if isinstance(config, str) else (config or {})
                )
            if "commitMessage" in body:
                current["commitMessage"] = body["commitMessage"]
            if "meta" in body:
                current["meta"] = body["meta"]
            if "status" in body:
                current["status"] = body["status"]
            if body.get("production"):
                for item in versions.values():
                    item["production"] = False
                current["production"] = True
            current["updatedAt"] = _TIMESTAMP
            return 200, current
        if self.command == "DELETE":
            if not self._write_auth_ok():
                return 403, {"errorMessage": "Write requires user API key."}
            versions.pop(version_id)
            return 204, None
        return 405, {"errorMessage": "method not allowed"}

    def do_GET(self) -> None:
        status, data = self._route()
        self._send_json(status, data)

    def do_POST(self) -> None:
        status, data = self._route()
        self._send_json(status, data)

    def do_PUT(self) -> None:
        status, data = self._route()
        self._send_json(status, data)

    def do_DELETE(self) -> None:
        status, data = self._route()
        self._send_json(status, data)


class LocalServer:
    def __init__(self) -> None:
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def url(self) -> str:
        if self._httpd is None:
            raise RuntimeError("server is not running")
        host, port = self._httpd.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        _Handler.agents = {DEFAULT_AGENT_ID: _default_agent()}
        _Handler.documents = {}
        _Handler.sessions = {}
        _Handler.messages = {}
        _Handler.memories = {}
        prompt_id = "prm_customer_support"
        prompt = {
            "promptId": prompt_id,
            "name": "Customer Support",
            "handle": "customer-support",
            "description": "Customer Support Prompt",
        }
        v1 = {
            "id": "prv_v1",
            "name": "Customer Support",
            "handle": "customer-support",
            "description": "Customer Support Prompt",
            "version": 1,
            "type": "text",
            "content": "You are a helpful assistant v1\n{{ctx}}",
            "config": {"model": "gpt3"},
            "labels": [],
            "commitMessage": "initial",
            "commitHash": "ba506ac20c11",
            "meta": None,
            "status": "active",
            "production": True,
            "createdAt": _TIMESTAMP,
            "updatedAt": _TIMESTAMP,
        }
        v2 = {
            "id": "prv_v2",
            "name": "Customer Support",
            "handle": "customer-support",
            "description": "Customer Support Prompt",
            "version": 2,
            "type": "text",
            "content": "You are a helpful assistant v2\n{{ctx}}",
            "config": {"model": "gpt3"},
            "labels": ["latest"],
            "commitMessage": "v2",
            "commitHash": "ba506ac20c12",
            "meta": None,
            "status": "active",
            "production": False,
            "createdAt": _TIMESTAMP,
            "updatedAt": _TIMESTAMP,
        }
        _Handler.prompts = {prompt_id: prompt}
        _Handler.prompt_versions = {prompt_id: {"prv_v1": v1, "prv_v2": v2}}
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._thread = Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
