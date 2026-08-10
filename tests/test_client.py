# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import httpx
import pytest

from pctx0 import (
    AccessKeyPrincipal,
    MemorySearchResults,
    MessageSearchResults,
    Pctx0Client,
    knowledge,
)
from local_server import (
    DEFAULT_AGENT_ID,
    DEFAULT_WORKSPACE_ACCESS_KEY,
    DEFAULT_WORKSPACE_ID,
)


def test_health(client: Pctx0Client) -> None:
    assert client.health() == {"status": "ok"}


def test_me_access_key(client: Pctx0Client) -> None:
    principal = client.me.get()
    assert isinstance(principal, AccessKeyPrincipal)
    assert principal.principal_type == "access_key"
    assert principal.access_key.workspace_id == DEFAULT_WORKSPACE_ID
    assert principal.access_key.name == "Agent runtime"
    assert "CAN_LIST_AGENTS" in principal.access_key.permissions


def test_me_invalid_access_key(client: Pctx0Client, base_url: str) -> None:
    with pytest.raises(httpx.HTTPStatusError):
        with Pctx0Client(
            base_url=base_url,
            access_key="bad-access-key",
            workspace_id=DEFAULT_WORKSPACE_ID,
        ) as bad_client:
            bad_client.me.get()


def test_standalone_me_client(base_url: str) -> None:
    from pctx0 import me

    with me(
        access_key=DEFAULT_WORKSPACE_ACCESS_KEY,
        base_url=base_url,
    ) as client:
        principal = client.get()
        assert isinstance(principal, AccessKeyPrincipal)


def test_knowledge_delete(client: Pctx0Client) -> None:
    uploaded = client.knowledge.upload(
        file=("policy.md", b"# Refund policy", "text/markdown"),
        title="Refund policy",
        labels={"team": "support"},
    )
    assert client.knowledge.delete(uploaded.id) is None


def test_knowledge_upload_dict_labels(client: Pctx0Client) -> None:
    uploaded = client.knowledge.upload(
        file=("policy.md", b"# Refund policy", "text/markdown"),
        title="Refund policy",
        labels={"team": "support", "category": "policy"},
    )
    assert uploaded.labels == ["team=support", "category=policy"]
    assert client.knowledge.delete(uploaded.id) is None


def test_agent_list_and_get(client: Pctx0Client) -> None:
    agents = client.agent.list()
    assert agents.total >= 1
    assert agents.agents[0].name == "Support bot"
    assert agents.agents[0].configs.memory_pipeline is False

    agent = client.agent.get(DEFAULT_AGENT_ID)
    assert agent.id == DEFAULT_AGENT_ID
    assert agent.kind == "unmanaged"
    assert agent.configs.memory_pipeline is False


def test_agent_create_update_delete(client: Pctx0Client) -> None:
    created = client.agent.create(name="Bot", description="Test bot")
    assert created.name == "Bot"
    assert created.configs.memory_pipeline is False

    with_pipeline = client.agent.create(
        name="Pipeline bot",
        description="Uses memory pipeline",
        memory_pipeline=True,
    )
    assert with_pipeline.configs.memory_pipeline is True

    updated = client.agent.update(
        created.id,
        name="Renamed bot",
        description="Updated description",
        memory_pipeline=True,
    )
    assert updated.name == "Renamed bot"
    assert updated.configs.memory_pipeline is True

    disabled = client.agent.update(
        created.id,
        name="Renamed bot",
        description="Updated description",
        memory_pipeline=False,
    )
    assert disabled.configs.memory_pipeline is False

    assert client.agent.delete(created.id) is None
    assert client.agent.delete(with_pipeline.id) is None


def test_document_list_search_upload(client: Pctx0Client, tmp_path) -> None:
    doc_path = tmp_path / "policy.md"
    doc_path.write_text("# Refund policy\n30 day window.", encoding="utf-8")

    uploaded = client.document.upload(
        file=doc_path,
        title="Refund policy",
        labels={"team": "support", "category": "policy"},
    )
    assert uploaded.title == "Refund policy"
    assert uploaded.status == "processing"

    listed = client.document.list()
    assert listed.total == 1
    assert listed.documents[0].id == uploaded.id

    results = client.document.search(
        query="refund policy",
        labels={"team": "support"},
        limit=5,
    )
    assert len(results.results) == 1
    assert results.results[0].score == 0.87

    assert client.document.delete(uploaded.id) is None


def test_document_exists(client: Pctx0Client, tmp_path) -> None:
    doc_path = tmp_path / "policy.md"
    doc_path.write_text("# Refund policy\n30 day window.", encoding="utf-8")
    labels = {"team": "support", "category": "policy"}

    assert client.document.exists(file=doc_path, labels=labels) is None

    uploaded = client.document.upload(
        file=doc_path,
        title="Refund policy",
        labels=labels,
    )
    found = client.document.exists(file=doc_path, labels=labels)
    assert found is not None
    assert found.id == uploaded.id
    assert found.checksum == uploaded.checksum

    assert (
        client.document.exists(
            file=doc_path,
            labels={"team": "other"},
        )
        is None
    )

    changed = tmp_path / "policy.md"
    changed.write_text("# Refund policy\nUpdated text.", encoding="utf-8")
    assert client.document.exists(file=changed, labels=labels) is None

    assert client.document.delete(uploaded.id) is None


def test_prompt_get_latest(client: Pctx0Client) -> None:
    prompt = client.prompt.get_by_name("customer-support")
    assert prompt.handle == "customer-support"
    assert prompt.version == 2
    assert prompt.content == "You are a helpful assistant v2\n{{ctx}}"
    assert str(prompt) == prompt.content


def test_prompt_get_with_version(client: Pctx0Client) -> None:
    prompt = client.prompt.get_by_name("customer-support", version="v1")
    assert prompt.version == 1
    assert prompt.content == "You are a helpful assistant v1\n{{ctx}}"


@pytest.mark.parametrize("version", ["latest", "production"])
def test_prompt_get_named_versions(client: Pctx0Client, version: str) -> None:
    prompt = client.prompt.get_by_name("customer-support", version=version)
    assert prompt.handle == "customer-support"
    if version == "latest":
        assert prompt.version == 2
    else:
        assert prompt.version == 1


def test_prompt_compile(client: Pctx0Client) -> None:
    prompt = client.prompt.get_by_name("customer-support")
    assert prompt.compile(ctx="Ahmed") == "You are a helpful assistant v2\nAhmed"


def test_prompt_get_requires_workspace(client: Pctx0Client, base_url: str) -> None:
    with Pctx0Client(
        access_key=DEFAULT_WORKSPACE_ACCESS_KEY,
        base_url=base_url,
    ) as bare_client:
        with pytest.raises(ValueError, match="workspace_id"):
            bare_client.prompt.get_by_name("customer-support")


def test_standalone_prompt_client(base_url: str) -> None:
    from pctx0 import prompt

    with prompt(
        base_url=base_url,
        access_key=DEFAULT_WORKSPACE_ACCESS_KEY,
        workspace_id=DEFAULT_WORKSPACE_ID,
    ) as client:
        fetched = client.get_by_name("customer-support")
        assert fetched.version == 2


def test_prompt_crud_and_versions(client: Pctx0Client) -> None:
    created = client.prompt.create(
        name="Mara Guide",
        type="text",
        content="You know Mara Ellison.",
        description="Answers questions about Mara",
        config={"tone": "friendly"},
        commit_message="initial",
        meta={"source": "examples"},
    )
    assert created.name == "Mara Guide"
    assert created.handle == "mara-guide"
    assert created.version_count == 1

    fetched = client.prompt.get(created.prompt_id)
    assert fetched.prompt_id == created.prompt_id

    listed = client.prompt.list()
    assert any(item.prompt_id == created.prompt_id for item in listed.prompts)

    version = client.prompt.create_version(
        created.prompt_id,
        type="text",
        content="You know Mara Ellison well.",
        commit_message="v2",
        production=True,
    )
    assert version.version == 2
    assert version.production is True

    versions = client.prompt.list_versions(created.prompt_id)
    assert versions.total == 2

    got = client.prompt.get_version(created.prompt_id, version.id)
    assert got.content == "You know Mara Ellison well."

    updated = client.prompt.update_version(
        created.prompt_id,
        version.id,
        content="You know Mara Ellison very well.",
        status="active",
        production=True,
    )
    assert updated.content == "You know Mara Ellison very well."

    by_name = client.prompt.get_by_name("mara-guide", version="production")
    assert by_name.id == version.id

    assert client.prompt.delete_version(created.prompt_id, version.id) is None
    assert client.prompt.delete(created.prompt_id) is None


@pytest.mark.parametrize(
    "attr",
    [
        "agent",
        "document",
        "knowledge",
        "me",
        "memory",
        "message",
        "prompt",
        "session",
    ],
)
def test_resources_share_http_client(client: Pctx0Client, attr: str) -> None:
    resource = getattr(client, attr)
    assert resource._http is client._http


def test_sends_access_key_header(base_url: str) -> None:
    with pytest.raises(httpx.HTTPStatusError):
        with Pctx0Client(access_key="wrong-key", base_url=base_url) as client:
            client.me.get()


def test_standalone_knowledge_client(base_url: str, tmp_path) -> None:
    doc_path = tmp_path / "notes.txt"
    doc_path.write_text("hello", encoding="utf-8")

    with knowledge(
        base_url=base_url,
        access_key=DEFAULT_WORKSPACE_ACCESS_KEY,
        workspace_id=DEFAULT_WORKSPACE_ID,
    ) as client:
        uploaded = client.upload(file=doc_path, title="Notes")
        assert uploaded.status == "processing"
        assert client.delete(uploaded.id) is None


def test_session_flow(client: Pctx0Client) -> None:
    created = client.session.create(
        DEFAULT_AGENT_ID,
        external_id="thread-123",
        title="Support chat",
    )
    assert created.external_id == "thread-123"
    assert created.title == "Support chat"

    fetched = client.session.get(DEFAULT_AGENT_ID, created.id)
    assert fetched.id == created.id

    by_labels = client.session.get_by_labels(DEFAULT_AGENT_ID, external_id="thread-123")
    assert by_labels.id == created.id

    listed = client.session.list(DEFAULT_AGENT_ID)
    assert listed.total == 1

    updated = client.session.update(
        DEFAULT_AGENT_ID,
        external_id="thread-123",
        title="Renamed chat",
        new_labels={"userId": "42"},
    )
    assert updated.title == "Renamed chat"
    assert updated.labels == {"userId": "42"}


def test_message_flow(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-msg")
    session_id = session.id

    message = client.message.create(
        DEFAULT_AGENT_ID,
        session_id,
        {
            "role": "user",
            "content": "Hello",
            "meta": {"source": "test", "channel": "web"},
        },
    )
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.meta == {"source": "test", "channel": "web"}

    listed = client.message.list(DEFAULT_AGENT_ID, session_id)
    assert listed.total == 1
    assert listed.messages[0].id == message.id

    fetched = client.message.get(DEFAULT_AGENT_ID, session_id, message.id)
    assert fetched.content == "Hello"

    updated = client.message.update(
        DEFAULT_AGENT_ID,
        session_id,
        message.id,
        content="Updated",
        role="assistant",
        meta={"source": "test", "edited": True},
    )
    assert updated.content == "Updated"
    assert updated.role == "assistant"
    assert updated.meta == {"source": "test", "edited": True}

    assert client.message.delete(DEFAULT_AGENT_ID, session_id, message.id) is None


def test_message_batch_create(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-msg-batch")
    session_id = session.id

    created = client.message.create(
        DEFAULT_AGENT_ID,
        session_id,
        [
            {
                "role": "user",
                "content": "Hello",
                "meta": {"source": "batch", "channel": "web"},
            },
            {
                "role": "assistant",
                "content": "Hi there",
                "meta": {"model": "gpt-4", "tokens": 12},
            },
        ],
    )
    assert len(created) == 2
    assert created[0].meta == {"source": "batch", "channel": "web"}
    assert created[1].meta == {"model": "gpt-4", "tokens": 12}

    assert (
        client.message.delete(DEFAULT_AGENT_ID, session_id, [m.id for m in created])
        is None
    )
    assert client.message.list(DEFAULT_AGENT_ID, session_id).total == 0


def test_message_add(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-msg-add")
    session_id = session.id

    created = client.message.create(
        DEFAULT_AGENT_ID,
        session_id,
        [
            {"role": "user", "content": "I'm a vegetarian and allergic to nuts."},
            {
                "role": "assistant",
                "content": "Got it! I'll remember your dietary preferences.",
            },
        ],
    )
    assert len(created) == 2
    assert created[0].role == "user"
    assert created[1].role == "assistant"

    listed = client.message.list(DEFAULT_AGENT_ID, session_id)
    assert listed.total == 2
    assert [m.id for m in listed.messages] == [m.id for m in created]


def test_message_search(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-msg-search")
    created = client.message.create(
        DEFAULT_AGENT_ID,
        session.id,
        [
            {"role": "user", "content": "Let's revisit the pricing discussion."},
            {"role": "assistant", "content": "The trial starts next week."},
        ],
    )

    results = client.message.search(
        DEFAULT_AGENT_ID,
        session.id,
        query="pricing discussion",
        limit=1,
    )

    assert isinstance(results, MessageSearchResults)
    assert len(results.results) == 1
    assert results.results[0].id == created[0].id
    assert results.results[0].role == "user"
    assert results.results[0].score == 0.91
    assert results.results[0].text == "Let's revisit the pricing discussion."


def test_memory_flow(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-mem")
    session_id = session.id

    memory = client.memory.create(
        DEFAULT_AGENT_ID,
        session_id,
        {
            "kind": "fact",
            "content": "User is in Cairo",
            "meta": {"confidence": 0.9, "source": "onboarding"},
        },
    )
    assert memory.kind == "fact"
    assert memory.content == "User is in Cairo"
    assert memory.meta == {"confidence": 0.9, "source": "onboarding"}

    listed = client.memory.list(DEFAULT_AGENT_ID, session_id)
    assert listed.total == 1

    fetched = client.memory.get(DEFAULT_AGENT_ID, session_id, memory.id)
    assert fetched.content == "User is in Cairo"

    updated = client.memory.update(
        DEFAULT_AGENT_ID,
        session_id,
        memory.id,
        content="User is in Cairo, Egypt",
        meta={"confidence": 0.95, "verified": True},
    )
    assert updated.content == "User is in Cairo, Egypt"
    assert updated.meta == {"confidence": 0.95, "verified": True}

    assert client.memory.delete(DEFAULT_AGENT_ID, session_id, memory.id) is None


def test_memory_batch_create(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-mem-batch")
    session_id = session.id

    created = client.memory.create(
        DEFAULT_AGENT_ID,
        session_id,
        [
            {
                "kind": "fact",
                "content": "User prefers dark mode",
                "meta": {"confidence": 0.95, "source": "onboarding"},
            },
            {"kind": "summary", "content": "Discussed billing setup"},
        ],
    )
    assert len(created) == 2
    assert created[0].meta == {"confidence": 0.95, "source": "onboarding"}
    assert created[1].meta == {}

    assert (
        client.memory.delete(DEFAULT_AGENT_ID, session_id, [m.id for m in created])
        is None
    )
    assert client.memory.list(DEFAULT_AGENT_ID, session_id).total == 0


def test_memory_search(client: Pctx0Client) -> None:
    session = client.session.create(DEFAULT_AGENT_ID, external_id="thread-mem-search")
    created = client.memory.create(
        DEFAULT_AGENT_ID,
        session.id,
        [
            {"kind": "preference", "content": "User preferences include dark mode."},
            {"kind": "fact", "content": "User is in Cairo."},
        ],
    )

    results = client.memory.search(
        DEFAULT_AGENT_ID,
        session.id,
        query="user preferences",
    )

    assert isinstance(results, MemorySearchResults)
    assert len(results.results) == 1
    assert results.results[0].id == created[0].id
    assert results.results[0].kind == "preference"
    assert results.results[0].score == 0.88
    assert results.results[0].text == "User preferences include dark mode."


def test_meta_helpers() -> None:
    from pctx0.utils import (
        build_memory_batch_payload,
        build_message_batch_payload,
        encode_item,
        stringify_meta,
    )

    assert stringify_meta({"source": "sdk"}) == '{"source": "sdk"}'
    assert stringify_meta(None) is None

    assert (
        encode_item({"role": "user", "content": "Hi", "meta": {"source": "import"}})[
            "meta"
        ]
        == '{"source": "import"}'
    )

    message_payload = build_message_batch_payload(
        [{"role": "user", "content": "Hi", "meta": {"source": "import"}}]
    )
    assert message_payload["messages"][0]["meta"] == '{"source": "import"}'

    memory_payload = build_memory_batch_payload(
        [{"kind": "fact", "content": "Prefers dark mode", "meta": {"source": "import"}}]
    )
    assert memory_payload["memories"][0]["meta"] == '{"source": "import"}'


def test_session_delete(client: Pctx0Client) -> None:
    client.session.create(DEFAULT_AGENT_ID, external_id="thread-del")
    assert client.session.delete(DEFAULT_AGENT_ID, external_id="thread-del") is None
    with pytest.raises(httpx.HTTPStatusError):
        client.session.get_by_labels(DEFAULT_AGENT_ID, external_id="thread-del")
