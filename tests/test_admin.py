import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.models.user import User, UserRole

client = TestClient(app)

PASSWORD = "correct-horse-battery"


def _login_as(email: str, role: UserRole = UserRole.USER) -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    if role is not UserRole.USER:
        # There is no API for granting a role - that is the point of the
        # route under test - so promote straight in the database.
        with SessionLocal() as session:
            session.execute(update(User).where(User.email == email).values(role=role))
            session.commit()
    token = client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_route_without_a_token_is_401() -> None:
    assert client.get("/admin/users").status_code == 401


@pytest.mark.integration
def test_member_is_403_on_admin_route() -> None:
    response = client.get("/admin/users", headers=_login_as("sam@example.com"))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Admin role required"


@pytest.mark.integration
def test_admin_lists_every_user_without_hashes() -> None:
    _login_as("sam@example.com")
    admin = _login_as("root@example.com", role=UserRole.ADMIN)

    response = client.get("/admin/users", headers=admin)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {u["email"] for u in body["users"]} == {
        "sam@example.com",
        "root@example.com",
    }
    assert "password_hash" not in response.text


@pytest.mark.integration
def test_demoted_admin_loses_access_on_the_same_token() -> None:
    # Role is read from the database per request, not baked into the token.
    admin = _login_as("root@example.com", role=UserRole.ADMIN)
    with SessionLocal() as session:
        session.execute(
            update(User)
            .where(User.email == "root@example.com")
            .values(role=UserRole.USER)
        )
        session.commit()
    assert client.get("/admin/users", headers=admin).status_code == 403
