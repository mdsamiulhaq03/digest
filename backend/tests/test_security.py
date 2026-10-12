import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def _sign(claims: dict, secret: str | None = None) -> str:
    return jwt.encode(
        claims, secret or get_settings().jwt_secret, algorithm=JWT_ALGORITHM
    )


def test_hash_is_argon2id_and_never_the_password() -> None:
    password_hash = hash_password("correct horse battery staple")
    assert password_hash.startswith("$argon2id$")
    assert "correct horse" not in password_hash


def test_same_password_hashes_differently_each_time() -> None:
    # A per-hash salt is what stops one precomputed table cracking every user.
    assert hash_password("secret-password") != hash_password("secret-password")


def test_verify_password_accepts_right_and_rejects_wrong() -> None:
    password_hash = hash_password("secret-password")
    assert verify_password(password_hash, "secret-password") is True
    assert verify_password(password_hash, "wrong-password") is False


def test_verify_password_rejects_unusable_hash() -> None:
    assert verify_password("!", "anything") is False


def test_token_round_trip_returns_user_id() -> None:
    user_id = uuid.uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id


def test_token_carries_an_expiry() -> None:
    claims = jwt.decode(
        create_access_token(uuid.uuid4()),
        get_settings().jwt_secret,
        algorithms=[JWT_ALGORITHM],
    )
    lifetime = claims["exp"] - claims["iat"]
    assert lifetime == get_settings().access_token_expire_minutes * 60


def test_expired_token_is_rejected() -> None:
    past = datetime.now(UTC) - timedelta(hours=2)
    token = _sign(
        {"sub": str(uuid.uuid4()), "iat": past, "exp": past + timedelta(hours=1)}
    )
    with pytest.raises(TokenExpiredError):
        decode_access_token(token)


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        "",
        # Signed with someone else's key.
        _sign(
            {"sub": str(uuid.uuid4()), "iat": 0, "exp": 2**31},
            secret="an-attacker-secret-that-is-at-least-32-chars",
        ),
        # Valid signature but no expiry - must not be accepted forever.
        _sign({"sub": str(uuid.uuid4()), "iat": 0}),
        # Valid signature but the subject is not a user id.
        _sign({"sub": "admin", "iat": 0, "exp": 2**31}),
    ],
    ids=["garbage", "empty", "wrong-key", "no-exp", "bad-sub"],
)
def test_untrustworthy_tokens_are_rejected(token: str) -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_unsigned_alg_none_token_is_rejected() -> None:
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "iat": 0, "exp": 2**31}, None, algorithm="none"
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
