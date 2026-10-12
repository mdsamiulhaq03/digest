from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.main import app
from app.routers.dependencies import get_active_user, get_job_queue
from tests.factories import RecordingQueue, make_user


def _truncate() -> None:
    with SessionLocal() as session:
        session.execute(text("TRUNCATE users, documents CASCADE"))
        session.commit()


@pytest.fixture(autouse=True)
def clean_database(request: pytest.FixtureRequest) -> Iterator[None]:
    """Integration tests share one real database, so give each a clean slate.
    Without this they accumulate rows forever and can never assert on exact
    contents. Tests without the marker never touch the DB, so they skip it
    entirely - that keeps them runnable in CI, which has no Postgres yet."""
    needs_db = request.node.get_closest_marker("integration") is not None
    if needs_db:
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
