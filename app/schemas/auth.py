import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# The upper bound is a denial-of-service guard, not a policy: argon2 hashes
# whatever it is given, and a multi-megabyte "password" is free CPU for an
# attacker.
MAX_PASSWORD_LENGTH = 128


class RegisterRequest(BaseModel):
    """Request body for creating an account."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=MAX_PASSWORD_LENGTH)


class LoginRequest(BaseModel):
    """Request body for exchanging credentials for an access token."""

    email: EmailStr
    # No minimum here: login checks a password, it doesn't set one.
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)


class TokenResponse(BaseModel):
    """An access token and how long it stays valid."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(..., description="Seconds until the token expires")


class UserResponse(BaseModel):
    """A user as the API shows it. The password hash never leaves the server."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """Every account, for admins."""

    users: list[UserResponse]
    total: int
