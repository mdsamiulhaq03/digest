"""Demo logins: off by default, and when on, a one-click way into a demo user
or demo admin that no real account can be confused with."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import Settings, get_settings
from app.core.db import SessionLocal
from app.main import app
from app.models.user import User
from app.schemas.auth import RegisterRequest

client = TestClient(app)


@pytest.fixture
def demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "demo_accounts", True)


def _demo_login(role: str):
    return client.post("/auth/demo/login", json={"role": role})


def _bearer(token_response) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_response.json()['access_token']}"}


def test_the_setting_is_off_unless_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_ACCOUNTS", raising=False)
    assert Settings(_env_file=None).demo_accounts is False


def test_demo_routes_do_not_exist_while_off(monkeypatch: pytest.MonkeyPatch) -> None:
    # Set explicitly: the local Compose stack turns demo mode on.
    monkeypatch.setattr(get_settings(), "demo_accounts", False)
    assert client.get("/auth/demo").status_code == 404
    assert _demo_login("user").status_code == 404


def test_lists_the_demo_accounts(demo_mode: None) -> None:
    response = client.get("/auth/demo")
    assert response.status_code == 200
    assert response.json() == {
        "accounts": [
            {"role": "user", "email": "demo@digest.local"},
            {"role": "admin", "email": "admin@digest.local"},
        ]
    }


def test_only_known_roles_can_be_asked_for(demo_mode: None) -> None:
    assert _demo_login("superuser").status_code == 422


@pytest.mark.parametrize("email", ["demo@digest.local", "admin@digest.local"])
def test_nobody_can_register_a_demo_address(email: str) -> None:
    """What stops a demo login from landing in a real person's account."""
    with pytest.raises(ValueError):
        RegisterRequest(email=email, password="correct-horse-battery")


@pytest.mark.integration
def test_demo_user_login_gives_an_ordinary_user(demo_mode: None) -> None:
    token = _demo_login("user")
    assert token.status_code == 200
    me = client.get("/auth/me", headers=_bearer(token)).json()
    assert me["email"] == "demo@digest.local"
    assert me["role"] == "user"
    assert client.get("/admin/users", headers=_bearer(token)).status_code == 403


@pytest.mark.integration
def test_demo_admin_login_can_use_admin_routes(demo_mode: None) -> None:
    token = _demo_login("admin")
    me = client.get("/auth/me", headers=_bearer(token)).json()
    assert me["role"] == "admin"
    assert client.get("/admin/users", headers=_bearer(token)).status_code == 200


@pytest.mark.integration
def test_each_demo_account_is_created_once(demo_mode: None) -> None:
    first = client.get("/auth/me", headers=_bearer(_demo_login("user"))).json()
    second = client.get("/auth/me", headers=_bearer(_demo_login("user"))).json()
    assert first["id"] == second["id"]
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.integration
def test_a_demo_account_cannot_be_logged_into_with_a_password(demo_mode: None) -> None:
    """Login validates the email like registration does, so a .local address
    is refused before any password is checked - the button is the only way in.
    (The stored password is random as well, as a second line.)"""
    _demo_login("user")
    response = client.post(
        "/auth/login",
        json={"email": "demo@digest.local", "password": "anything-at-all"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["loc"] == ["body", "email"]
