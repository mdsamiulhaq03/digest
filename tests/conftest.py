from tests.database import TEST_REDIS_DB, create_test_database, use_test_database

# Before any app import below: app.core.db builds its engine at import time.
use_test_database()

from collections.abc import Iterator
from pathlib import Path

import pytest
import redis
from sqlalchemy import text

from app.core.cache import JsonCache
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.queue import get_redis
from app.main import app
from app.routers.dependencies import get_active_user, get_cache, get_job_queue
from app.services import job_processor
from tests.factories import FakeRedis, RecordingQueue, make_user


def _truncate() -> None:
    with SessionLocal() as session:
        session.execute(text("TRUNCATE users, documents CASCADE"))
        session.commit()


@pytest.fixture(scope="session")
def test_database() -> None:
    """Created and migrated once per run, by the first test that needs it."""
    create_test_database()


@pytest.fixture(autouse=True)
def clean_database(request: pytest.FixtureRequest) -> Iterator[None]:
    """Integration tests share one test database, so give each a clean slate.
    Without this they accumulate rows and can never assert on exact contents.
    Tests without the marker never touch the DB, so they skip it entirely -
    that keeps them runnable on a machine with no Postgres."""
    needs_db = request.node.get_closest_marker("integration") is not None
    if needs_db:
        request.getfixturevalue("test_database")
        _truncate()
    yield
    if needs_db:
        _truncate()


@pytest.fixture
def as_some_user() -> Iterator[None]:
    """Stand in for a logged-in user on tests that never reach the database -
    the real token check has to load the user, which needs Postgres. The auth
    chain itself is covered in test_auth_dependencies.py."""
    app.dependency_overrides[get_active_user] = lambda: make_user()
    yield
    app.dependency_overrides.pop(get_active_user)


@pytest.fixture(autouse=True)
def cache_redis(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeRedis]:
    """Every test gets its own empty in-memory cache, so tests never read
    entries left by another test, and never write into the dev Redis."""
    fake = FakeRedis()
    cache = JsonCache(fake, get_settings().document_cache_ttl_seconds)
    app.dependency_overrides[get_cache] = lambda: cache
    monkeypatch.setattr(job_processor, "get_document_cache", lambda: cache)
    yield fake
    app.dependency_overrides.pop(get_cache)


@pytest.fixture
def real_redis() -> Iterator[redis.Redis]:
    """The tests' own Redis database, empty at the start and end of the test."""
    client = get_redis()
    # Guard: never flush a Redis database that isn't the tests' own.
    assert client.connection_pool.connection_kwargs["db"] == TEST_REDIS_DB
    client.flushdb()
    yield client
    client.flushdb()


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Uploads land in a per-test temp folder, never the real volume."""
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    return tmp_path


@pytest.fixture
def queue() -> Iterator[RecordingQueue]:
    """Swap Redis for a queue that records what was enqueued."""
    recording = RecordingQueue()
    app.dependency_overrides[get_job_queue] = lambda: recording
    yield recording
    app.dependency_overrides.pop(get_job_queue)
