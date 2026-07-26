# Copyright 2026 Actx0. All rights reserved.
# License can be found in the LICENSE file.

from __future__ import annotations

import os
from collections.abc import Generator

import pytest

from pctx0 import Pctx0Client, knowledge
from local_server import (
    DEFAULT_WORKSPACE_ACCESS_KEY,
    DEFAULT_WORKSPACE_ID,
    LocalServer,
)


@pytest.fixture(scope="session")
def base_url() -> Generator[str, None, None]:
    env_url = os.environ.get("PCTX0_BASE_URL")
    if env_url:
        yield env_url.rstrip("/")
        return

    server = LocalServer()
    server.start()
    try:
        yield server.url
    finally:
        server.stop()


@pytest.fixture
def client(base_url: str) -> Generator[Pctx0Client, None, None]:
    with Pctx0Client(
        base_url=base_url,
        access_key=DEFAULT_WORKSPACE_ACCESS_KEY,
        workspace_id=DEFAULT_WORKSPACE_ID,
    ) as client:
        yield client
