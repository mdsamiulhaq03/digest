# Digest

Document ingestion and insight service, built phase by phase.

## Repository layout

```
backend/            FastAPI API and worker (Python)
  app/              the application - routers, services, repositories, models
  tests/            pytest suite
  scripts/          measurement scripts
  Dockerfile        API/worker image (runtime and dev targets)
frontend/           Next.js web app (TypeScript, App Router, Tailwind)
  src/app/          pages and route handlers
  src/lib/api.ts    the only code that calls the API
  Dockerfile        web image
docker-compose.yml  runs everything together
.github/workflows/  CI
```

Each side has its own dependencies and tooling (`backend/requirements*.txt` and `backend/pyproject.toml`; `frontend/package.json`). Commands below say which folder to run them from.

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

## Caching

`GET /documents/{id}` is served from Redis when it can be. Nothing else is cached.

- **Key:** `doc:v1:{owner_id}:{document_id}`. The owner is part of the key, so another user's lookup can only miss — the cache can never hand one user someone else's document. The `v1` prefix is bumped whenever the response shape changes, so a deploy never serves entries in an old shape.
- **Only complete documents are cached:** pasted text, or an upload whose job has succeeded. A document still processing is about to change, so it's always read from Postgres. When a job succeeds, the worker also deletes that document's key, as a backstop.
- **Identity is checked first.** The token and the account are verified against Postgres before the cache is consulted, so a disabled or deleted user is refused even if their document is cached.
- **TTL: 1 hour** (`DOCUMENT_CACHE_TTL_SECONDS`). A document never changes once complete and the API can't edit one, so the TTL only bounds changes made *outside* the app (an edit in psql). Those can stay hidden for up to an hour — the same window a revoked user's 60-minute token keeps working.
- **Redis down?** Reads fall back to Postgres; the request still succeeds. After a Redis failure the cache (and the upload queue) skip Redis for 5 seconds, because with its container stopped even resolving the hostname takes ~3.5s — without that, every request would pay it.

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

Services raise domain exceptions from `backend/app/core/exceptions.py` (`DocumentNotFoundError`, etc.) and never mention HTTP. Handlers registered in `backend/app/main.py` map those to status codes at the edge — so the status code for a rule lives in exactly one place, and services stay testable without a `TestClient`.

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

This starts five services: `web` (the Next.js frontend), `app` (the API), `worker`, `db` (Postgres) and `redis`. The web app is at http://localhost:3000 and the API at http://localhost:8000, with hot reload on changes under `backend/app/`. Postgres data and uploaded files persist across `docker compose down` via named volumes. Migrations run automatically before the server starts, including on a completely fresh volume; the worker waits for the API to be healthy, so it never starts against an unmigrated database. Redis is only reachable inside Compose.

### Without Docker

Requires `DATABASE_URL` to point at a reachable Postgres, and requires migrations to be applied manually (the auto-migrate-on-startup behavior only happens inside the Docker image). The simplest way is to run just the database via Compose and connect to it over its published port:

```powershell
docker compose up db
cd backend
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

## Frontend

The browser only ever talks to Next.js. Next.js calls the API server-side, over the Compose network, through one helper: `frontend/src/lib/api.ts`. That way the browser never learns where the API lives, the browser needs no CORS access to it, and (from Phase 8) the login token can sit in an httpOnly cookie that no script on the page can read. `API_URL` is a server-only setting; never rename it with a `NEXT_PUBLIC_` prefix, or it gets baked into the JavaScript sent to the browser.

`GET http://localhost:3000/api/health` checks that whole path, browser → Next.js → API: `{"frontend": "ok", "api": "ok"}`, or `"api": "unreachable"` when the API is down. The page itself still renders without the API.

**Develop the frontend outside Docker.** Compose's `web` service runs the production build, without hot reload: on Docker Desktop, file-change events from Windows don't reach the container, so Next.js never sees an edit (the Next.js docs recommend the same). With the rest of the stack running in Compose:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local   # API_URL=http://localhost:8000
npm run dev                          # http://localhost:3000, hot reload
```

Stop the `web` container first (`docker compose stop web`) or `npm run dev` can't take port 3000. Run `npm run dev -- --port 3001` to keep both.

## Checks

A `Makefile` defines these targets (requires `make`, e.g. `choco install make`); the underlying commands work just as well run directly if you don't have `make` installed:

| Target | What it runs | Needs |
|---|---|---|
| `make up` | `docker compose up --build` | Docker |
| `make test` | `docker compose run --rm app pytest` | Docker (starts Postgres and Redis itself) |
| `make lint` | `ruff check .` + `ruff format --check .` in `backend/`; `npm run lint` + `npm run typecheck` in `frontend/` | A venv with `backend/requirements-dev.txt`; `npm install` in `frontend/` |

`make test` runs the full suite inside a container wired to Postgres and Redis. Add `--cov` (`docker compose run --rm app pytest --cov`) for the coverage report.

**Tests never touch your development data.**

- **Postgres:** the suite uses its own database on the same server, named after yours with `_test` appended (`digest_test`). It is dropped, recreated and migrated with `alembic upgrade head` at the start of every run, so the schema always comes from the migrations and a broken migration fails the run. Integration tests truncate their tables before and after each test.
- **Redis:** tests use logical database 15 (the app uses 0), so the development worker never takes a test's job off the queue.
- **Everything else:** uploads go to a temporary folder. Most tests swap the queue for an in-memory recorder and the cache for a fresh in-memory store; the tests marked `integration` use the real Postgres and Redis.

Tests marked `integration` need Postgres and Redis. Compose doesn't publish Redis's port, so outside Docker, `pytest -m "not integration"` runs just the tests that need neither.

**Test order is random.** `pytest-randomly` shuffles the tests on every run, so a test that only passes after another one fails early. The run's header prints the seed (`Using --randomly-seed=12905295`); to replay a failure in the same order, run `pytest -p randomly --randomly-seed=12905295`. To run in file order while debugging, use `-p no:randomly`.

### CI

Every push to `main` and every pull request runs five GitHub Actions jobs:

| Job | Fails when |
|---|---|
| `lint` | `ruff check .` finds a problem in `backend/` |
| `format` | `ruff format --check .` would change a file in `backend/` |
| `test` | any backend test fails, or coverage drops below **97%** (Postgres 16 and Redis 7 run as service containers, so the whole suite runs, integration tests included) |
| `frontend` | `npm run lint`, `npm run typecheck` or `npm run build` fails in `frontend/` |
| `image` | the backend `runtime` or `dev` image, or the frontend image, doesn't build; the backend runtime image runs as root or contains pytest or ruff, or fails to migrate an empty database and serve `/health` and `POST /auth/register`; the frontend image runs as root, or `/api/health` through Next.js doesn't reach the API |

**Coverage** counts branches as well as lines, and the threshold lives in `backend/pyproject.toml` with two decimals (`fail_under = 97`, `precision = 2`). With whole numbers, 96.5% would round up and pass. Raise it as coverage grows, never lower it. The `test` job's summary page shows the coverage table for each run.

### Responsiveness under upload load

```powershell
cd backend
python scripts/measure_latency.py --base-url http://localhost:8000
```

Times `GET /health` while idle and while 10 concurrent ~10 MB uploads run (5 rounds by default), and prints median, p95 and max for each. It registers a throwaway `latency-…@example.com` user, so run it against a development stack only. Measured from Windows, every request carries ~45 ms of Docker port-forwarding overhead; for clean numbers, copy the script into the `app` container and run it there.

### Cache: cold vs warm reads

```powershell
cd backend
python scripts/measure_cache.py --base-url http://localhost:8000
```

Creates 25 text and 25 CSV documents (needs the worker running), then reads each one twice: first a cache miss, then a hit. Client-side timings include transport overhead the cache can't affect, so compare the server-side `duration_ms` on the `request handled` access-log lines instead — measured that way, a miss took a median 10.6 ms and a hit 4.9 ms. Also uses a throwaway `latency-…@example.com` user.

## Images

`backend/Dockerfile` has two final targets. `runtime` is the default, so a plain `docker build backend` produces the lean production image with no test or lint tooling in it. Compose builds `target: dev`, which adds `pytest`/`ruff` on top so `make test` can run inside the container.

`frontend/Dockerfile` builds Next.js's standalone server: the compiled app and only the `node_modules` files it needs, with no source and no dev dependencies, running as the unprivileged `node` user.

CI builds all three on every pull request, so a broken Dockerfile fails the PR rather than the deploy.

## Database migrations

New migration after changing a model:

```powershell
docker compose run --rm app alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `backend/app/alembic/versions/` before applying — autogenerate doesn't always get it right. Then `docker compose up` (or `alembic upgrade head`) applies it.
