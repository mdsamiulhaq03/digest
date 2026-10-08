"""Identity against the real app and real Postgres - no fakes, no overrides."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import JWT_ALGORITHM
from app.main import app
from app.models.document import Document
from app.models.insight import Insight
from app.models.user import User

client = TestClient(app)

PASSWORD = "correct-horse-battery"


def _register_and_login(email: str) -> tuple[str, dict[str, str]]:
    user_id = client.post(
        "/auth/register", json={"email": email, "password": PASSWORD}
    ).json()["id"]
    token = client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    ).json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def _count(model: type) -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model))


@pytest.mark.integration
def test_expired_token_is_401_on_a_real_route() -> None:
    user_id, _ = _register_and_login("sam@example.com")
    past = datetime.now(UTC) - timedelta(hours=2)
    expired = jwt.encode(
        {"sub": user_id, "iat": past, "exp": past + timedelta(hours=1)},
        get_settings().jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/documents", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Authentication token has expired"


@pytest.mark.integration
def test_malformed_token_is_401_on_a_real_route() -> None:
    _register_and_login("sam@example.com")
    response = client.get("/documents", headers={"Authorization": "Bearer abc.def"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid authentication token"


@pytest.mark.integration
def test_token_forged_for_another_user_id_is_401() -> None:
    _register_and_login("sam@example.com")
    # Right shape, wrong key: what an attacker who guessed a user id would send.
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "iat": 0, "exp": 2**31},
        "an-attacker-secret-that-is-at-least-32-chars",
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/documents", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


@pytest.mark.integration
def test_deleting_a_user_deletes_their_documents_and_kills_their_token() -> None:
    sam_id, sam = _register_and_login("sam@example.com")
    _, alex = _register_and_login("alex@example.com")
    client.post("/documents", json={"title": "Sam's", "text": "One."}, headers=sam)
    client.post("/documents", json={"title": "Alex's", "text": "Two."}, headers=alex)
    assert _count(Document) == 2

    with SessionLocal() as session:
        session.execute(delete(User).where(User.id == uuid.UUID(sam_id)))
        session.commit()

    # ON DELETE CASCADE: documents, then their insights, go with the owner...
    assert _count(Document) == 1
    assert _count(Insight) == 1
    # ...nobody else's are touched...
    assert client.get("/documents", headers=alex).json()["total"] == 1
    # ...and a still-unexpired token for the deleted account is worthless.
    assert client.get("/documents", headers=sam).status_code == 401
