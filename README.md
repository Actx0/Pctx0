### Pctx0 Client

Python Client for the Actx0 Platform.

#### Install

```bash
uv add pctx0
```

#### Usage

```python
from pctx0 import knowledge

client = knowledge(
    access_key="your-access-key",
    workspace_id="your-workspace-id",
)
client.list()
client.close()
```

Or use the full client when you need multiple API areas:

```python
from pctx0 import Pctx0Client

client = Pctx0Client(
    access_key="your-access-key",
    workspace_id="your-workspace-id",
)
client.health()
client.knowledge.list()
client.close()
```

#### Development

```bash
uv sync
uv format --check --preview-features format
uv run pytest
```

Tests start a local mock API server automatically. To run against your own local pctx0 server:

```bash
PCTX0_BASE_URL=http://127.0.0.1:8000 uv run pytest
```
