### Pctx0 Client

Python Client for the Actx0 Platform.

#### Install

```bash
uv add pctx0
```

For document chunking helpers:

```bash
uv add "pctx0[chunk]"
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

#### Chunking

Requires `pctx0[chunk]`. Split long docs before upload with Actx0 defaults
(`recursive`, size `2000`, overlap `400`):

```python
from pctx0 import chunk, chunk_text

chunks = chunk_text(long_document)
# or: chunks = chunk("notes.md")

for part in chunks:
    client.knowledge.upload(
        file=part.as_file(filename=f"notes-{part.index:04d}.txt"),
        title=f"Notes part {part.index + 1}",
    )
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
