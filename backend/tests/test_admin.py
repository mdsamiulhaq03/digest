import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import UserRole
from tests.factories import login_as, set_role

client = TestClient(app)


def test_admin_route_without_a_token_is_401() -> None:
    assert client.get("/admin/users").status_code == 401


@pytest.mark.integration
def test_member_is_403_on_admin_route() -> None:
    sam = login_as("sam@example.com")
    response = client.get("/admin/users", headers=sam.headers)
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Admin role required"


@pytest.mark.integration
def test_admin_lists_every_user_without_hashes() -> None:
    login_as("sam@example.com")
    root = login_as("root@example.com", role=UserRole.ADMIN)

    response = client.get("/admin/users", headers=root.headers)
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
    root = login_as("root@example.com", role=UserRole.ADMIN)
    set_role("root@example.com", UserRole.USER)
    assert client.get("/admin/users", headers=root.headers).status_code == 403
