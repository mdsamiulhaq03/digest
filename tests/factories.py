"""Builders shared across the test suite, so a change to how users are made or
logged in happens in one place."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.models.user import User, UserRole

PASSWORD = "correct-horse-battery"

_client = TestClient(app)


def make_user(**overrides: object) -> User:
    """An in-memory User for tests that never touch the database."""
    fields = {
        "id": uuid.uuid4(),
        "email": f"{uuid.uuid4().hex}@example.com",
        "password_hash": "unused",
        "role": UserRole.USER,
        "is_active": True,
        "created_at": datetime.now(UTC),
        **overrides,
    }
    return User(**fields)


@dataclass(frozen=True)
class LoggedInUser:
    id: str
    headers: dict[str, str]


def login_as(email: str, role: UserRole = UserRole.USER) -> LoggedInUser:
    """Register a real user through the API, optionally promote them, and log in."""
    user_id = _client.post(
        "/auth/register", json={"email": email, "password": PASSWORD}
    ).json()["id"]
    if role is not UserRole.USER:
        set_role(email, role)
    token = _client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    ).json()["access_token"]
    return LoggedInUser(id=user_id, headers={"Authorization": f"Bearer {token}"})


def set_role(email: str, role: UserRole) -> None:
    # There is no API for granting a role, so tests change it in the database.
    with SessionLocal() as session:
        session.execute(update(User).where(User.email == email).values(role=role))
        session.commit()
