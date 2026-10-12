"""The document cache against a real Redis.

test_document_cache.py proves the caching rules with an in-memory stand-in;
these prove the real thing behaves the same: entries really land in Redis
with their TTL, a hit really skips Postgres, and the worker's delete really
removes the key.
"""

import json
import uuid
from pathlib import Path

import pytest
import redis
from fastapi.testclient import TestClient

from app.core.cache import document_key, get_cache_client, get_document_cache
from app.core.config import get_settings
from app.main import app
from app.repositories.document_repository import DocumentRepository
from app.routers.dependencies import get_cache
from app.services import job_processor
from tests.database import TEST_REDIS_DB
from tests.factories import FakeRedis, RecordingQueue, login_as, upload

client = TestClient(app)


@pytest.fixture
def real_cache(
    real_redis: redis.Redis, cache_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> redis.Redis:
    """Swap conftest's in-memory cache for the app's real one. Returns a
    client on the same Redis database, for looking inside it."""
    assert get_cache_client().connection_pool.connection_kwargs["db"] == TEST_REDIS_DB
    cache = get_document_cache()
    app.dependency_overrides[get_cache] = lambda: cache
    monkeypatch.setattr(job_processor, "get_document_cache", lambda: cache)
    return real_redis


def _forbid_database_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_db(*args: object) -> None:
        raise AssertionError("read went to Postgres instead of the cache")

    monkeypatch.setattr(DocumentRepository, "get_for_owner", no_db)


@pytest.mark.integration
def test_a_miss_stores_the_document_and_the_next_read_is_a_hit(
    real_cache: redis.Redis, monkeypatch: pytest.MonkeyPatch
) -> None:
    sam = login_as("sam@example.com")
    document_id = client.post(
        "/documents",
        json={"title": "Cached", "text": "Some text to cache."},
        headers=sam.headers,
    ).json()["id"]
    key = document_key(uuid.UUID(sam.id), uuid.UUID(document_id))
    assert real_cache.exists(key) == 0

    miss = client.get(f"/documents/{document_id}", headers=sam.headers)

    assert miss.status_code == 200
    assert json.loads(real_cache.get(key)) == miss.json()
    ttl = get_settings().document_cache_ttl_seconds
    assert ttl - 5 <= real_cache.ttl(key) <= ttl

    _forbid_database_reads(monkeypatch)
    hit = client.get(f"/documents/{document_id}", headers=sam.headers)
    assert hit.status_code == 200
    assert hit.json() == miss.json()


@pytest.mark.integration
def test_an_upload_is_cached_only_once_its_job_has_finished(
    real_cache: redis.Redis, queue: RecordingQueue, upload_dir: Path
) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()
    document_url = f"/documents/{accepted['document_id']}"
    key = document_key(uuid.UUID(sam.id), uuid.UUID(accepted["document_id"]))

    # Still processing: served from Postgres, never stored.
    in_progress = client.get(document_url, headers=sam.headers).json()
    assert in_progress["csv_insights"] is None
    assert real_cache.exists(key) == 0

    # Whatever might be under the key when the job finishes, the worker
    # removes it - here, a stale copy planted by hand.
    real_cache.set(key, json.dumps(in_progress))
    job_processor.process_job(uuid.UUID(accepted["job_id"]), queue)
    assert real_cache.exists(key) == 0

    finished = client.get(document_url, headers=sam.headers).json()
    assert finished["csv_insights"]["row_count"] == 2
    assert json.loads(real_cache.get(key)) == finished
