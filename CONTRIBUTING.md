# Contributing

Thanks for helping improve the Actx0 Python client (`pctx0`).

## Development setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Checks

```bash
uv format --check --preview-features format
uv run pytest
```

Tests start a local mock API server automatically. To run against a local Actx0 API:

```bash
PCTX0_BASE_URL=http://127.0.0.1:8000 uv run pytest
```

Examples default to the production API at [https://app.actx0.com](https://app.actx0.com).

## Pull requests

1. Open an issue first for larger changes when useful.
2. Keep changes focused and match existing style.
3. Add or update tests when behavior changes.
4. Ensure format and tests pass before requesting review.
5. Fill out the pull request template.

## Reporting bugs

Use the bug report issue template and include:

- Client version / commit
- Python version and OS
- Minimal reproduction steps
- Expected vs actual behavior

Do not include access keys, tokens, or other secrets.

## Code of conduct

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions

Reach out at [hello@actx0.com](mailto:hello@actx0.com) or open a discussion/issue on GitHub.
