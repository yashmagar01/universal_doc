# templix-server

FastAPI application for Templix: local API, SQLite storage, blob store, job runner/SSE, vault, and
the PyMuPDF-backed ingestion pipeline. The project quick-start, gates, and licence notes live in
the [root README](../../README.md).

## Run

```powershell
uv sync --extra dev
uv run python -m templix.serve
```

The server binds to `127.0.0.1:8000` by default (`TEMPLIX_PORT`, `TEMPLIX_HOME`, `TEMPLIX_TOKEN`
configure it) and prints a one-time session URL.

## Test

```powershell
uv run ruff check .
uv run pyright .
uv run pytest -q
```
