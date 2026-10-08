"""Builders shared across the test suite, so a change to how users are made or
logged in happens in one place."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from httpx import Response
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.models.user import User, UserRole

PASSWORD = "correct-horse-battery"
CSV_BYTES = b"name,age\nada,36\nalan,41\n"

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


def upload(
    headers: dict[str, str], filename: str = "people.csv", body: bytes = CSV_BYTES
) -> Response:
    return _client.post(
        "/documents/upload", files={"file": (filename, body)}, headers=headers
    )


class RecordingQueue:
    """Captures enqueued ids instead of talking to Redis."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.job_ids: list[uuid.UUID] = []

    def enqueue(self, job_id: uuid.UUID) -> None:
        if self.fail:
            raise RedisConnectionError("redis is down")
        self.job_ids = [*self.job_ids, job_id]
