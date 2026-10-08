"""The auth dependency chain, exercised over HTTP with no database.

A throwaway app mounts one route per dependency and swaps the user repository
for an in-memory fake, so every token case runs in CI.
"""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.error_handlers import app_error_handler
from app.core.exceptions import AppError
from app.core.security import JWT_ALGORITHM, create_access_token
from app.models.user import User, UserRole
from app.routers.dependencies import (
    get_active_user,
    get_current_user,
    get_user_repository,
    require_admin,
)
from tests.factories import make_user


class FakeUserRepository:
    def __init__(self, users: list[User]) -> None:
        self._users = {user.id: user for user in users}

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)


MEMBER = make_user()
ADMIN = make_user(role=UserRole.ADMIN)
DISABLED = make_user(is_active=False)

app = FastAPI()
app.add_exception_handler(AppError, app_error_handler)
app.dependency_overrides[get_user_repository] = lambda: FakeUserRepository(
    [MEMBER, ADMIN, DISABLED]
)


@app.get("/me")
def me(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": str(user.id)}


@app.get("/active")
def active(user: User = Depends(get_active_user)) -> dict[str, str]:
    return {"id": str(user.id)}


@app.get("/admin")
def admin(user: User = Depends(require_admin)) -> dict[str, str]:
    return {"id": str(user.id)}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _assert_401(response, message: str) -> None:
    assert response.status_code == 401
    assert response.json()["error"]["message"] == message
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_no_token_is_401(client: TestClient) -> None:
    _assert_401(client.get("/me"), "Invalid authentication token")


def test_wrong_scheme_is_401(client: TestClient) -> None:
    response = client.get("/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    _assert_401(response, "Invalid authentication token")


def test_malformed_token_is_401(client: TestClient) -> None:
    _assert_401(
        client.get("/me", headers=_auth("not.a.jwt")), "Invalid authentication token"
    )


def test_expired_token_is_401(client: TestClient) -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    token = jwt.encode(
        {"sub": str(MEMBER.id), "iat": past, "exp": past + timedelta(hours=1)},
        get_settings().jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    _assert_401(
        client.get("/me", headers=_auth(token)), "Authentication token has expired"
    )


def test_token_for_deleted_user_is_401(client: TestClient) -> None:
    token = create_access_token(uuid.uuid4())
    _assert_401(client.get("/me", headers=_auth(token)), "Invalid authentication token")


def test_valid_token_resolves_the_user(client: TestClient) -> None:
    response = client.get("/me", headers=_auth(create_access_token(MEMBER.id)))
    assert response.status_code == 200
    assert response.json() == {"id": str(MEMBER.id)}


def test_disabled_user_is_403_on_active_routes(client: TestClient) -> None:
    token = create_access_token(DISABLED.id)
    response = client.get("/active", headers=_auth(token))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Account is disabled"


def test_disabled_admin_check_runs_after_active_check(client: TestClient) -> None:
    response = client.get("/admin", headers=_auth(create_access_token(DISABLED.id)))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Account is disabled"


def test_member_is_403_on_admin_route(client: TestClient) -> None:
    response = client.get("/admin", headers=_auth(create_access_token(MEMBER.id)))
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Admin role required"


def test_admin_reaches_admin_route(client: TestClient) -> None:
    response = client.get("/admin", headers=_auth(create_access_token(ADMIN.id)))
    assert response.status_code == 200
    assert response.json() == {"id": str(ADMIN.id)}
