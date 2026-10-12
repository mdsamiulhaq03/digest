# Digest

Document ingestion and insight service, built phase by phase.

## API

- `POST /auth/register` - create an account (email + password, 8–128 chars)
- `POST /auth/login` - exchange credentials for a bearer token
- `POST /documents` - submit title + text, get insights back immediately
- `POST /documents/upload` - upload a `.txt` or `.csv` file (max 10 MB); insights are computed in the background
- `GET /jobs/{id}` - poll a background job
- `GET /documents` - list **your** documents, newest first
- `GET /documents/{id}` - fetch one of **your** documents
- `GET /admin/users` - list every account (admin only)
- `GET /health` - health check

Everything under `/documents`, `/jobs` and `/admin` needs an `Authorization: Bearer <token>` header.

Text insights (pasted text and `.txt` uploads):

- character, word, unique word, sentence and paragraph counts
- average word length
- top 10 words
- estimated reading time

CSV insights (`.csv` uploads): row and column counts, and per column its name, null count, inferred type (`integer`, `float`, `boolean`, `string` or `empty`), and min/max/mean for numeric columns.

> **Note:** documents, jobs and insights are stored in Postgres. Schema is versioned with Alembic migrations, which run automatically on container startup.

## Uploads and background jobs

```powershell
curl.exe -X POST localhost:8000/documents/upload -H "Authorization: Bearer eyJ..." -F "file=@sales.csv"
# -> 202 Accepted, Location: /jobs/7c1e...
#    {"document_id": "...", "job_id": "7c1e...", "status_url": "/jobs/7c1e..."}

curl.exe localhost:8000/jobs/7c1e... -H "Authorization: Bearer eyJ..."
# -> {"state": "succeeded", "attempts": 1, "last_error": null, "document_url": "/documents/...", ...}
```

The upload returns as soon as the file is stored; poll `status_url` until `state` is `succeeded` (insights are then on the document) or `failed` (`last_error` says why).

- Files are stored under `UPLOAD_DIR` by document id, never by their original name, so names can't collide or escape the directory.
- Only `.txt` and `.csv` are accepted (**415** otherwise), decided by extension rather than the client's `Content-Type`. Over 10 MB is **413**. Files must be UTF-8.
- Jobs go `queued → running → succeeded | failed`. An unexpected failure is retried up to 3 attempts; a file that can never succeed (not UTF-8, missing) fails at once.
- A separate `worker` container takes job ids from a Redis list. Postgres holds the jobs themselves, so if Redis or the worker dies, a sweeper (on worker startup, then every minute) finds stuck or never-queued jobs and puts them back.
- `docker compose stop worker` lets the job in progress finish before the worker exits.

The worker doesn't hot-reload: after changing worker-side code, run `docker compose restart worker`.

## Authentication

```powershell
curl.exe -X POST localhost:8000/auth/register -H "Content-Type: application/json" `
  -d '{\"email\": \"sam@example.com\", \"password\": \"correct-horse-battery\"}'

curl.exe -X POST localhost:8000/auth/login -H "Content-Type: application/json" `
  -d '{\"email\": \"sam@example.com\", \"password\": \"correct-horse-battery\"}'
# -> {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}

curl.exe localhost:8000/documents -H "Authorization: Bearer eyJ..."
```

In the interactive docs, click **Authorize** and paste the `access_token`.

- Passwords are stored as argon2id hashes and never returned or logged.
- Tokens are HS256 JWTs signed with `JWT_SECRET` and expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60). They carry only the user id. Role and active status are read from the database on every request, so disabling or demoting someone takes effect immediately.
- Documents belong to the user who created them. Another user's document returns **404**, exactly like one that doesn't exist, so ids can't be probed.
- A missing, malformed or expired token gets **401** (with `WWW-Authenticate: Bearer`). A disabled account or a non-admin on an admin route gets **403**.
- Deleting a user deletes their documents. Disabling them (`is_active = false`) is the reversible option.
- There is no endpoint for granting the admin role. Promote a user directly in the database:

  ```powershell
  docker compose exec db psql -U digest -d digest -c "UPDATE users SET role = 'admin' WHERE email = 'sam@example.com';"
  ```
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

A validation failure adds a `details` key holding the per-field errors (`type`, `loc`, `msg`, but never the rejected value itself, which could be a password); it is omitted entirely otherwise, rather than sent as `null`. `request_id` matches the `X-Request-ID` response header and is the value to quote when reporting a problem.

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
# Replace JWT_SECRET in .env with a real random value - the app won't start without one:
python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up --build
```

This starts four services: `app` (the API), `worker`, `db` (Postgres) and `redis`. The API is available at http://localhost:8000, with hot reload on changes under `app/`. Postgres data and uploaded files persist across `docker compose down` via named volumes. Migrations run automatically before the server starts, including on a completely fresh volume; the worker waits for the API to be healthy, so it never starts against an unmigrated database. Redis is only reachable inside Compose.

### Without Docker

Requires `DATABASE_URL` to point at a reachable Postgres, and requires migrations to be applied manually (the auto-migrate-on-startup behavior only happens inside the Docker image). The simplest way is to run just the database via Compose and connect to it over its published port:

```powershell
docker compose up db
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://digest:digest@localhost:5433/digest"
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:REDIS_URL = "redis://localhost:6379/0"   # needs a Redis you can reach locally
$env:UPLOAD_DIR = "$PWD\uploads"; New-Item -ItemType Directory -Force uploads | Out-Null
alembic upgrade head
uvicorn app.main:app --reload
python -m app.worker   # in a second terminal, to process uploads
```

Compose doesn't publish Redis's port, so outside Docker you'll need your own Redis for uploads; everything else works without it.

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

Outside Docker, `pytest -m "not integration"` runs only the tests that don't touch the database — that's also what CI runs, since Postgres isn't wired into CI yet (that's Phase 7). Tests never need Redis: they swap the queue for an in-memory recorder, and uploads go to a temporary folder.

### Responsiveness under upload load

```powershell
python scripts/measure_latency.py --base-url http://localhost:8000
```

Times `GET /health` while idle and while 10 concurrent ~10 MB uploads run (5 rounds by default), and prints median, p95 and max for each. It registers a throwaway `latency-…@example.com` user, so run it against a development stack only. Measured from Windows, every request carries ~45 ms of Docker port-forwarding overhead; for clean numbers, copy the script into the `app` container and run it there.

## Images

The Dockerfile has two final targets. `runtime` is the default, so a plain `docker build .` produces the lean production image with no test or lint tooling in it. Compose builds `target: dev`, which adds `pytest`/`ruff` on top so `make test` can run inside the container.

## Database migrations

New migration after changing a model:

```powershell
docker compose run --rm app alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `app/alembic/versions/` before applying — autogenerate doesn't always get it right. Then `docker compose up` (or `alembic upgrade head`) applies it.
