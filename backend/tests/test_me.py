import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.models.user import User
from tests.factories import login_as

client = TestClient(app)


@pytest.mark.integration
def test_me_returns_the_tokens_owner() -> None:
    sam = login_as("sam@example.com")
    response = client.get("/auth/me", headers=sam.headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == sam.id
    assert body["email"] == "sam@example.com"
    assert body["role"] == "user"
    assert "password_hash" not in body


def test_me_without_a_token_is_401() -> None:
    assert client.get("/auth/me").status_code == 401


@pytest.mark.integration
def test_me_for_a_disabled_account_is_403() -> None:
    sam = login_as("sam@example.com")
    with SessionLocal() as session:
        session.execute(update(User).values(is_active=False))
        session.commit()
    assert client.get("/auth/me", headers=sam.headers).status_code == 403
