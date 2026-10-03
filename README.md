# Digest

Document ingestion and insight service, built phase by phase.

## API

- `POST /documents` - submit title + text, get insights back
- `GET /documents` - list all documents
- `GET /documents/{id}` - fetch one document
- `GET /health` - health check

Insights per document:

- character, word, unique word, sentence and paragraph counts
- average word length
- top 10 words
- estimated reading time

> **Note:** documents and insights are stored in Postgres. Schema is versioned with Alembic migrations, which run automatically on container startup.

## Errors

Every failure returns the same shape, whatever caused it — a known application error, a rejected payload, or an unhandled crash:

```json
{
  "error": {
    "message": "Document 0f9c... not found",
    "request_id": "8c1f4e2a-..."
  }
}
```

A validation failure adds a `details` key holding the per-field errors; it is omitted entirely otherwise, rather than sent as `null`. `request_id` matches the `X-Request-ID` response header and is the value to quote when reporting a problem.

Services raise domain exceptions from `app/core/exceptions.py` (`DocumentNotFoundError`, etc.) and never mention HTTP. Handlers registered in `app/main.py` map those to status codes at the edge — so the status code for a rule lives in exactly one place, and services stay testable without a `TestClient`.

A crash returns `"Internal server error"` and nothing else. The exception type, message and traceback go to the logs only: an exception string can easily carry a file path, a query or a connection string.

## Observability

Logs are JSON on stdout, one object per line, at `LOG_LEVEL` (default `INFO`). Nothing writes with `print`, and uvicorn's and SQLAlchemy's standard-library logs are funnelled through the same sink, so every line logged while serving a request is JSON.

Two sets of lines at boot are still plain text, both because they are emitted before the application is imported and logging is configured: Alembic's migration output (a separate process in the entrypoint) and the three lines from the `--reload` supervisor, which only exists in the dev image. Neither happens during request handling.

Each request gets an ID — taken from the client's `X-Request-ID` header if it sends one, otherwise generated — which is returned on the response and attached to **every** log line emitted while handling that request, including lines logged deep inside a service. It travels in a `contextvar`, not through function arguments, so no function signature has to mention it.

One access line is written per request with method, path, status and duration, including when the handler raised:

```json
{"message": "request handled", "extra": {"request_id": "8c1f...", "method": "GET",
 "path": "/documents/abc", "status_code": 404, "duration_ms": 3.62}}
```

Uvicorn's own access log is switched off rather than intercepted — it would be a second, less useful line for the same request.

To trace a failure: pull the `request_id` from the error response, then filter logs on it to get that request's access line and everything it logged along the way.

## Setup

### With Docker (recommended)

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API is available at http://localhost:8000, with hot reload on changes under `app/`. Postgres data persists across `docker compose down` via a named volume. Migrations run automatically before the server starts, including on a completely fresh volume.

### Without Docker

Requires `DATABASE_URL` to point at a reachable Postgres, and requires migrations to be applied manually (the auto-migrate-on-startup behavior only happens inside the Docker image). The simplest way is to run just the database via Compose and connect to it over its published port:

```powershell
docker compose up db
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://digest:digest@localhost:5433/digest"
alembic upgrade head
uvicorn app.main:app --reload
```

> `requirements.txt` is runtime-only and is what the production image installs. `requirements-dev.txt` pulls it in and adds `pytest`/`ruff`/`httpx` — use that one locally and in CI.

Note the host is `localhost` (not `db` — that only resolves inside the Compose network) and the port is `5433` (not Postgres's usual `5432`, in case you already have a local Postgres install using that port).

Interactive docs at http://localhost:8000/docs

## Checks

A `Makefile` defines these targets (requires `make`, e.g. `choco install make`); the underlying commands work just as well run directly if you don't have `make` installed:

| Target | What it runs | Needs |
|---|---|---|
| `make up` | `docker compose up --build` | Docker |
| `make test` | `docker compose run --rm app pytest` | Docker (spins up Postgres itself) |
| `make lint` | `ruff check .` + `ruff format --check .` | Local venv with `requirements-dev.txt` |

`make test` runs the full suite (including tests marked `integration`, which need a real database) inside a container wired to Postgres. Integration tests truncate their tables before and after each test, so they never leave rows behind.

Outside Docker, `pytest -m "not integration"` runs only the tests that don't touch the database — that's also what CI runs, since Postgres isn't wired into CI yet (that's Phase 7).

## Images

The Dockerfile has two final targets. `runtime` is the default, so a plain `docker build .` produces the lean production image with no test or lint tooling in it. Compose builds `target: dev`, which adds `pytest`/`ruff` on top so `make test` can run inside the container.

## Database migrations

New migration after changing a model:

```powershell
docker compose run --rm app alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `app/alembic/versions/` before applying — autogenerate doesn't always get it right. Then `docker compose up` (or `alembic upgrade head`) applies it.
