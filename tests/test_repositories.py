"""Repositories stage writes; only an explicit commit makes them stick. That
contract is what lets a service write several rows as one unit of work."""

import pytest
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository


def _user_count() -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(User))


@pytest.mark.integration
def test_uncommitted_create_is_rolled_back_when_the_session_closes() -> None:
    with SessionLocal() as session:
        created = UserRepository(session).create(
            User(email="sam@example.com", password_hash="x")
        )
        # The flush has already happened: the id and server defaults are set.
        assert created.id is not None
        assert created.created_at is not None
    assert _user_count() == 0


@pytest.mark.integration
def test_committed_create_persists() -> None:
    with SessionLocal() as session:
        repo = UserRepository(session)
        repo.create(User(email="sam@example.com", password_hash="x"))
        repo.commit()
    assert _user_count() == 1
