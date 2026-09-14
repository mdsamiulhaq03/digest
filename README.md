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

> **Note:** storage is in-memory. Restarting the server loses all data.

## Setup

### With Docker (recommended)

```powershell
New-Item -ItemType File -Path .env -ErrorAction SilentlyContinue
docker compose up --build
```

The API is available at http://localhost:8000, with hot reload on changes under `app/`.

> **Note:** `.env` isn't used by the app yet (no config to load) but `docker-compose.yml` requires the file to exist. An empty file is fine for now.

### Without Docker

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interactive docs at http://localhost:8000/docs

## Checks

```bash
pytest
ruff check .
ruff format .
```

Or, with Docker running:

```powershell
docker compose exec app pytest
docker compose exec app ruff check .
```
