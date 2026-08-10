#!/usr/bin/env python3
"""Create a client and print access key info via /api/v1/me.

uv run python examples/01_me.py
"""

from __future__ import annotations

from dataclasses import asdict
from pprint import pp

from pctx0 import Pctx0Client

ACCESS_KEY = "227fc70d-151c-4a7f-85e2-20ef147cbcc1"
WORKSPACE_ID = "adae803a-5b20-41c7-bd9b-304792bccabe"
BASE_URL = "https://app.actx0.com"


def main() -> None:
    client = Pctx0Client(
        access_key=ACCESS_KEY,
        workspace_id=WORKSPACE_ID,
        base_url=BASE_URL,
    )

    me = client.me.get()
    print("Access key info")
    print("=" * 40)
    pp(asdict(me.access_key), sort_dicts=False, width=100)
    client.close()


if __name__ == "__main__":
    main()
