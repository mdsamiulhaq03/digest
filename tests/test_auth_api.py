import pytest
from fastapi.testclient import TestClient

from app.core.request_context import REQUEST_ID_HEADER
from app.core.security import decode_access_token
from app.main import app
from tests.factories import PASSWORD

client = TestClient(app)

EMAIL = "sam@example.com"


def _register(email: str = EMAIL, password: str = PASSWORD):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_rejects_a_short_password() -> None:
    response = _register(password="short")
    assert response.status_code == 422


def test_rejected_password_is_never_echoed_back() -> None:
    response = _register(password="hunter2")
    assert response.status_code == 422
    assert "hunter2" not in response.text
    # The client still learns which field failed and why.
    detail = response.json()["error"]["details"][0]
    assert detail["loc"] == ["body", "password"]
    assert detail["msg"]


def test_register_rejects_an_invalid_email() -> None:
    response = _register(email="not-an-email")
    assert response.status_code == 422


def test_register_rejects_an_oversized_password() -> None:
    response = _register(password="x" * 129)
    assert response.status_code == 422


@pytest.mark.integration
def test_register_returns_the_user_without_the_hash() -> None:
    response = _register(email="Sam@Example.com")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == EMAIL
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.integration
def test_register_twice_returns_409() -> None:
    _register()
    response = _register(email=EMAIL.upper())
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Email is already registered"


@pytest.mark.integration
def test_login_returns_a_token_for_that_user() -> None:
    user_id = _register().json()["id"]
    response = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert str(decode_access_token(body["access_token"])) == user_id


@pytest.mark.integration
@pytest.mark.parametrize(
    ("email", "password"),
    [(EMAIL, "wrong-password"), ("nobody@example.com", PASSWORD)],
    ids=["wrong-password", "unknown-email"],
)
def test_bad_login_is_one_indistinguishable_401(email: str, password: str) -> None:
    _register()
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    # The extra header must not displace the request id from Phase 3.
    assert response.headers[REQUEST_ID_HEADER]
