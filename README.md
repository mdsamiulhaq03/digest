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
