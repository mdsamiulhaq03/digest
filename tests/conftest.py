from collections.abc import Iterator

import pytest
from sqlalchemy import text

from app.core.db import SessionLocal
from app.main import app
from app.routers.dependencies import get_active_user
from tests.factories import make_user


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
