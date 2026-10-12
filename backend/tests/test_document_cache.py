"""Every way the document cache could serve something untrue, and the test
that proves each one is closed. The `cache_redis` fixture (conftest) gives
each test an empty in-memory Redis it can inspect and tamper with."""

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import delete, update

from app.core import cache as cache_module
from app.core.cache import document_key
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.job_processor import process_job
from tests.factories import FakeRedis, LoggedInUser, RecordingQueue, login_as, upload

client = TestClient(app)


def _create_text_document(user: LoggedInUser, title: str = "Original") -> str:
    return client.post(
        "/documents",
        json={"title": title, "text": "Some text to cache."},
        headers=user.headers,
    ).json()["id"]


def _key(user: LoggedInUser, document_id: str) -> str:
    return document_key(uuid.UUID(user.id), uuid.UUID(document_id))


def _read(user: LoggedInUser, document_id: str):
    return client.get(f"/documents/{document_id}", headers=user.headers)


def _forbid_database_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_db(*args: object) -> None:
        raise AssertionError("read went to Postgres instead of the cache")

    monkeypatch.setattr(DocumentRepository, "get_for_owner", no_db)


def test_malformed_id_never_touches_the_cache(
    as_some_user: None, cache_redis: FakeRedis
) -> None:
    assert client.get("/documents/not-a-uuid").status_code == 404
    assert cache_redis.store == {}


@pytest.mark.integration
def test_first_read_is_stored_second_is_served_without_postgres(
    cache_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam)

    first = _read(sam, document_id)
    assert _key(sam, document_id) in cache_redis.store
    assert cache_redis.ttls[_key(sam, document_id)] == 3600

    _forbid_database_reads(monkeypatch)
    second = _read(sam, document_id)
    assert second.status_code == 200
    assert second.json() == first.json()


@pytest.mark.integration
def test_another_user_can_never_be_served_someone_elses_entry(
    cache_redis: FakeRedis,
) -> None:
    alice = login_as("alice@example.com")
    bob = login_as("bob@example.com")
    document_id = _create_text_document(alice)
    _read(alice, document_id)  # Alice's entry is now cached

    assert _read(bob, document_id).status_code == 404
    # Bob's lookup used his own key, which can only miss; nothing was stored
    # for him, and Alice's entry is the only one.
    assert list(cache_redis.store) == [_key(alice, document_id)]


@pytest.mark.integration
def test_upload_in_progress_is_never_cached_and_shows_insights_once_done(
    cache_redis: FakeRedis, upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()
    document_id = accepted["document_id"]

    assert _read(sam, document_id).json()["csv_insights"] is None
    assert cache_redis.store == {}  # still processing: not cached

    process_job(uuid.UUID(accepted["job_id"]), queue)

    done = _read(sam, document_id).json()
    assert done["csv_insights"]["row_count"] == 2
    assert _key(sam, document_id) in cache_redis.store  # complete: now cached


@pytest.mark.integration
def test_worker_removes_any_entry_for_a_document_it_finishes(
    cache_redis: FakeRedis, upload_dir: Path, queue: RecordingQueue
) -> None:
    # Belt and braces: if an in-progress copy were ever cached (a future bug,
    # or a rule change), finishing the job must not leave it behind.
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()
    key = _key(sam, accepted["document_id"])
    cache_redis.store = {key: json.dumps({"stale": True})}

    process_job(uuid.UUID(accepted["job_id"]), queue)

    assert key not in cache_redis.store
    assert _read(sam, accepted["document_id"]).json()["csv_insights"] is not None


@pytest.mark.integration
def test_disabled_user_is_refused_even_with_a_cached_document(
    cache_redis: FakeRedis,
) -> None:
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam)
    _read(sam, document_id)
    with SessionLocal() as session:
        session.execute(
            update(User).where(User.id == uuid.UUID(sam.id)).values(is_active=False)
        )
        session.commit()

    # Identity is checked against Postgres before the cache is consulted.
    assert _read(sam, document_id).status_code == 403


@pytest.mark.integration
def test_deleted_user_is_refused_even_with_a_cached_document(
    cache_redis: FakeRedis,
) -> None:
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam)
    _read(sam, document_id)
    with SessionLocal() as session:
        session.execute(delete(User).where(User.id == uuid.UUID(sam.id)))
        session.commit()

    assert _key(sam, document_id) in cache_redis.store  # still there...
    assert _read(sam, document_id).status_code == 401  # ...but never served


@pytest.mark.integration
def test_a_new_cache_version_ignores_every_old_entry(
    cache_redis: FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam, title="Real title")
    old_key = _key(sam, document_id)
    # An entry in an old response shape, as left by the previous deploy.
    cache_redis.store = {old_key: json.dumps({"title": "old shape"})}

    monkeypatch.setattr(cache_module, "CACHE_VERSION", "v2")
    response = _read(sam, document_id)

    assert response.json()["title"] == "Real title"
    assert _key(sam, document_id) != old_key


@pytest.mark.integration
def test_redis_down_falls_back_to_postgres(cache_redis: FakeRedis) -> None:
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam)
    cache_redis.error = RedisConnectionError("redis is down")

    response = _read(sam, document_id)
    assert response.status_code == 200
    assert response.json()["title"] == "Original"


@pytest.mark.integration
def test_known_limit_change_made_outside_the_app_waits_for_the_ttl(
    cache_redis: FakeRedis,
) -> None:
    """Not a bug fixed - a limit accepted on purpose, pinned so it can't change
    silently. The app has no way to edit a document, so the only way to change
    a cached one is directly in the database. That change stays invisible for
    up to the TTL, the same window a revoked user's token stays valid."""
    sam = login_as("sam@example.com")
    document_id = _create_text_document(sam, title="Before")
    _read(sam, document_id)
    with SessionLocal() as session:
        session.execute(
            update(Document)
            .where(Document.id == uuid.UUID(document_id))
            .values(title="Edited in psql")
        )
        session.commit()

    assert _read(sam, document_id).json()["title"] == "Before"
    ttl = cache_redis.ttls[_key(sam, document_id)]
    assert ttl == get_settings().document_cache_ttl_seconds == 3600
