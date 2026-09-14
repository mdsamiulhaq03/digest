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
