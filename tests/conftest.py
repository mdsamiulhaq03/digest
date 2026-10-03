from collections.abc import Iterator

import pytest
from sqlalchemy import text

from app.core.db import SessionLocal


def _truncate() -> None:
    with SessionLocal() as session:
        session.execute(text("TRUNCATE documents CASCADE"))
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
