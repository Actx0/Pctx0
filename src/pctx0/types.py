# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Required, TypedDict

MemoryKind = Literal["summary", "fact", "preference"]
MessageRole = Literal["system", "user", "assistant"]
PromptType = Literal["text", "chat"]
PromptStatus = Literal["active", "archived"]

FileInput = str | Path | tuple[str, bytes, str]

_TEMPLATE_VAR = re.compile(r"\{\{(\w+)\}\}")


class MessageInput(TypedDict, total=False):
    role: Required[MessageRole]
    content: Required[str]
    meta: dict[str, Any]


class MemoryInput(TypedDict, total=False):
    kind: Required[MemoryKind]
    content: Required[str]
    meta: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AgentConfigs:
    memory_pipeline: bool = False

    @classmethod
    def from_api(cls, data: dict[str, Any] | None) -> AgentConfigs:
        if not data:
            return cls()
        return cls(memory_pipeline=bool(data.get("memoryPipeline", False)))


@dataclass(frozen=True, slots=True)
class Agent:
    id: str
    workspace_id: str
    name: str
    kind: str
    prompt_id: str | None
    kb_labels: dict[str, str]
    handle: str
    description: str
    status: str
    configs: AgentConfigs
    created_at: str
    updated_at: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Agent:
        return cls(
            id=data["id"],
            workspace_id=data["workspaceId"],
            name=data["name"],
            kind=data.get("kind", "unmanaged"),
            prompt_id=data.get("promptId"),
            kb_labels=data.get("kbLabels", {}),
            handle=data["handle"],
            description=data["description"],
            status=data.get("status", "active"),
            configs=AgentConfigs.from_api(data.get("configs")),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
        )


@dataclass(frozen=True, slots=True)
class AgentList:
    agents: list[Agent]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AgentList:
        meta = data["_meta"]
        return cls(
            agents=[Agent.from_api(item) for item in data["agents"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class Session:
    id: str
    external_id: str
    workspace_id: str
    agent_id: str
    title: str
    status: str
    labels: dict[str, str]
    meta: dict[str, Any]
    created_at: str
    updated_at: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Session:
        return cls(
            id=data["id"],
            external_id=data["externalId"],
            workspace_id=data["workspaceId"],
            agent_id=data["agentId"],
            title=data.get("title", ""),
            status=data["status"],
            labels=data.get("labels", {}),
            meta=data.get("meta", {}),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
        )


@dataclass(frozen=True, slots=True)
class SessionList:
    sessions: list[Session]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SessionList:
        meta = data["_meta"]
        return cls(
            sessions=[Session.from_api(item) for item in data["sessions"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class Message:
    id: str
    session_id: str
    role: MessageRole
    content: str
    meta: dict[str, Any]
    created_at: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Message:
        return cls(
            id=data["id"],
            session_id=data["sessionId"],
            role=data["role"],
            content=data["content"],
            meta=data.get("meta", {}),
            created_at=data["createdAt"],
        )


@dataclass(frozen=True, slots=True)
class MessageList:
    messages: list[Message]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MessageList:
        meta = data["_meta"]
        return cls(
            messages=[Message.from_api(item) for item in data["messages"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class MessageSearchHit:
    id: str
    role: MessageRole
    score: float
    text: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MessageSearchHit:
        return cls(
            id=data["id"],
            role=data["role"],
            score=data["score"],
            text=data["text"],
        )


@dataclass(frozen=True, slots=True)
class MessageSearchResults:
    results: list[MessageSearchHit]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MessageSearchResults:
        return cls(
            results=[MessageSearchHit.from_api(item) for item in data["results"]],
        )


@dataclass(frozen=True, slots=True)
class Memory:
    id: str
    session_id: str
    kind: MemoryKind
    content: str
    meta: dict[str, Any]
    created_at: str
    updated_at: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Memory:
        return cls(
            id=data["id"],
            session_id=data["sessionId"],
            kind=data["kind"],
            content=data["content"],
            meta=data.get("meta", {}),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
        )


@dataclass(frozen=True, slots=True)
class MemoryList:
    memories: list[Memory]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MemoryList:
        meta = data["_meta"]
        return cls(
            memories=[Memory.from_api(item) for item in data["memories"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class MemorySearchHit:
    id: str
    kind: MemoryKind
    score: float
    text: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MemorySearchHit:
        return cls(
            id=data["id"],
            kind=data["kind"],
            score=data["score"],
            text=data["text"],
        )


@dataclass(frozen=True, slots=True)
class MemorySearchResults:
    results: list[MemorySearchHit]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MemorySearchResults:
        return cls(
            results=[MemorySearchHit.from_api(item) for item in data["results"]],
        )


@dataclass(frozen=True, slots=True)
class DocumentSize:
    value: int
    unit: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DocumentSize:
        return cls(value=data["value"], unit=data["unit"])


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    workspace_id: str
    title: str
    filename: str
    content_type: str
    checksum: str
    size: DocumentSize
    char_count: int
    labels: list[str]
    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Document:
        return cls(
            id=data["id"],
            workspace_id=data["workspaceId"],
            title=data["title"],
            filename=data["filename"],
            content_type=data["contentType"],
            checksum=data["checksum"],
            size=DocumentSize.from_api(data["size"]),
            char_count=data["charCount"],
            labels=data.get("labels", []),
            chunking_strategy=data["chunkingStrategy"],
            chunk_size=data["chunkSize"],
            chunk_overlap=data["chunkOverlap"],
            status=data["status"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
        )


@dataclass(frozen=True, slots=True)
class DocumentList:
    documents: list[Document]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DocumentList:
        meta = data["_meta"]
        return cls(
            documents=[Document.from_api(item) for item in data["documents"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class SearchHit:
    document_id: str
    chunk_id: str
    score: float
    text: str
    labels: dict[str, str]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SearchHit:
        return cls(
            document_id=data["documentId"],
            chunk_id=data["chunkId"],
            score=data["score"],
            text=data["text"],
            labels=data.get("labels", {}),
        )


@dataclass(frozen=True, slots=True)
class SearchResults:
    results: list[SearchHit]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SearchResults:
        return cls(
            results=[SearchHit.from_api(item) for item in data["results"]],
        )


@dataclass(frozen=True, slots=True)
class AccessKeyInfo:
    id: str
    workspace_id: str
    name: str
    permissions: list[str]
    created_at: str
    updated_at: str
    expires_at: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AccessKeyInfo:
        return cls(
            id=data["id"],
            workspace_id=data["workspaceId"],
            name=data["name"],
            permissions=data["permissions"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            expires_at=data.get("expiresAt"),
        )


@dataclass(frozen=True, slots=True)
class AccessKeyPrincipal:
    principal_type: Literal["access_key"]
    access_key: AccessKeyInfo

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> AccessKeyPrincipal:
        return cls(
            principal_type="access_key",
            access_key=AccessKeyInfo.from_api(data["accessKey"]),
        )


MePrincipal = AccessKeyPrincipal


@dataclass(frozen=True, slots=True)
class PromptInfo:
    """Prompt summary returned by list/create/get-by-id."""

    prompt_id: str
    name: str
    handle: str
    description: str
    version_count: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PromptInfo:
        return cls(
            prompt_id=data["promptId"],
            name=data["name"],
            handle=data["handle"],
            description=data.get("description", ""),
            version_count=data["versionCount"],
        )


@dataclass(frozen=True, slots=True)
class PromptList:
    prompts: list[PromptInfo]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PromptList:
        meta = data["_meta"]
        return cls(
            prompts=[PromptInfo.from_api(item) for item in data["prompts"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


@dataclass(frozen=True, slots=True)
class Prompt:
    """A prompt version returned by the API."""

    id: str
    name: str
    handle: str
    description: str
    version: int
    type: str
    content: str
    commit_hash: str
    status: str
    production: bool
    created_at: str
    updated_at: str
    config: dict[str, Any]
    labels: list[str]
    commit_message: str | None = None
    meta: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Prompt:
        config = data.get("config") or {}
        if isinstance(config, str):
            config = json.loads(config) if config else {}
        return cls(
            id=data["id"],
            name=data["name"],
            handle=data["handle"],
            description=data.get("description", ""),
            version=data["version"],
            type=data["type"],
            content=data["content"],
            commit_hash=data["commitHash"],
            status=data["status"],
            production=data["production"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            config=config if isinstance(config, dict) else {},
            labels=data.get("labels") or [],
            commit_message=data.get("commitMessage"),
            meta=data.get("meta"),
        )

    def compile(self, **variables: str) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in variables:
                raise KeyError(f"missing template variable: {key}")
            return variables[key]

        return _TEMPLATE_VAR.sub(replace, self.content)

    def __str__(self) -> str:
        return self.content


@dataclass(frozen=True, slots=True)
class PromptVersionList:
    versions: list[Prompt]
    limit: int
    offset: int
    total: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PromptVersionList:
        meta = data["_meta"]
        return cls(
            versions=[Prompt.from_api(item) for item in data["versions"]],
            limit=meta["limit"],
            offset=meta["offset"],
            total=meta["total"],
        )


# Backward-compatible alias
PromptVersion = Prompt
