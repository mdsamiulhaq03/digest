import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

# Pinned here, never read from config or from the token header: letting the
# token choose its own algorithm is how "alg: none" and HS/RS confusion
# attacks forge tokens.
JWT_ALGORITHM = "HS256"

# argon2-cffi's defaults are argon2id with the RFC 9106 low-memory profile.
# The parameters and salt are encoded into every hash it produces, so they can
# be raised later without breaking existing hashes.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        # A wrong password and an unusable stored hash (like the system
        # account's "!") both mean the same thing to a caller: not this user.
        return False


@lru_cache
def _decoy_hash() -> str:
    return _hasher.hash(secrets.token_urlsafe(32))


def spend_password_check(password: str) -> None:
    """Do the work of a password check against no account at all.

    Login calls this for an unknown email so the response takes as long as a
    wrong password would, instead of returning instantly and confirming the
    email has no account."""
    verify_password(_decoy_hash(), password)


def access_token_lifetime() -> timedelta:
    return timedelta(minutes=get_settings().access_token_expire_minutes)


def create_access_token(user_id: uuid.UUID) -> str:
    # Only the identity goes in the token. Role and active flag are read from
    # the database on every request, so a demotion or deactivation takes effect
    # immediately instead of when the token expires.
    now = datetime.now(UTC)
    claims = {"sub": str(user_id), "iat": now, "exp": now + access_token_lifetime()}
    return jwt.encode(claims, get_settings().jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Return the user id a token was issued to, or raise if it can't be trusted."""
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        return uuid.UUID(claims["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise InvalidTokenError() from exc
