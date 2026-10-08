import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import decode_access_token, hash_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth_service

PASSWORD = "correct-horse-battery"


class FakeUserRepository:
    """Stands in for UserRepository so the service is tested with no database."""

    def __init__(self, users: list[User] | None = None) -> None:
        self._users = {user.email: user for user in users or []}

    def create(self, user: User) -> User:
        if user.email in self._users:
            raise EmailAlreadyRegisteredError()
        stored = User(
            id=uuid.uuid4(),
            email=user.email,
            password_hash=user.password_hash,
            role="user",
            is_active=True,
            created_at=datetime.now(UTC),
        )
        self._users = {**self._users, stored.email: stored}
        return stored

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((u for u in self._users.values() if u.id == user_id), None)

    def get_by_email(self, email: str) -> User | None:
        return self._users.get(email)


def _existing_user(email: str = "sam@example.com", is_active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(PASSWORD),
        role="user",
        is_active=is_active,
        created_at=datetime.now(UTC),
    )


def test_register_stores_lowercased_email_and_a_hash() -> None:
    repo = FakeUserRepository()
    response = auth_service.register(
        RegisterRequest(email="Sam@Example.com", password=PASSWORD), repo
    )
    assert response.email == "sam@example.com"
    stored = repo.get_by_email("sam@example.com")
    assert stored is not None
    assert stored.password_hash != PASSWORD
    assert stored.password_hash.startswith("$argon2id$")


def test_register_response_never_contains_the_hash() -> None:
    response = auth_service.register(
        RegisterRequest(email="sam@example.com", password=PASSWORD),
        FakeUserRepository(),
    )
    assert "password_hash" not in response.model_dump()


def test_register_rejects_an_email_in_any_case() -> None:
    repo = FakeUserRepository([_existing_user("sam@example.com")])
    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(
            RegisterRequest(email="SAM@example.com", password=PASSWORD), repo
        )


def test_login_returns_a_token_for_the_user() -> None:
    user = _existing_user()
    response = auth_service.login(
        LoginRequest(email="sam@example.com", password=PASSWORD),
        FakeUserRepository([user]),
    )
    assert response.token_type == "bearer"
    assert response.expires_in > 0
    assert decode_access_token(response.access_token) == user.id


def test_login_is_case_insensitive_on_email() -> None:
    response = auth_service.login(
        LoginRequest(email="SAM@EXAMPLE.COM", password=PASSWORD),
        FakeUserRepository([_existing_user()]),
    )
    assert response.access_token


@pytest.mark.parametrize(
    ("email", "password", "is_active"),
    [
        ("sam@example.com", "wrong-password", True),
        ("nobody@example.com", PASSWORD, True),
        ("sam@example.com", PASSWORD, False),
    ],
    ids=["wrong-password", "unknown-email", "inactive-user"],
)
def test_login_failures_are_indistinguishable(
    email: str, password: str, is_active: bool
) -> None:
    repo = FakeUserRepository([_existing_user(is_active=is_active)])
    with pytest.raises(InvalidCredentialsError) as exc_info:
        auth_service.login(LoginRequest(email=email, password=password), repo)
    assert exc_info.value.message == "Invalid email or password"


def test_unknown_email_still_spends_a_password_check() -> None:
    with (
        patch.object(auth_service, "spend_password_check") as spend,
        pytest.raises(InvalidCredentialsError),
    ):
        auth_service.login(
            LoginRequest(email="nobody@example.com", password=PASSWORD),
            FakeUserRepository(),
        )
    spend.assert_called_once_with(PASSWORD)
