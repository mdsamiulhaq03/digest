"""One-click demo logins, for trying the app without registering.

Only while DEMO_ACCOUNTS is on. The accounts use .local addresses, which
registration refuses (a special-use domain), so a demo login can never land in
an account a real person signed up for. They are created on first use with a
random password nobody knows: the demo button is the only way in.
"""

import secrets

from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import DemoModeDisabledError, EmailAlreadyRegisteredError
from app.core.security import access_token_lifetime, create_access_token, hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.demo import DemoAccount, DemoAccountsResponse, DemoRole

DEMO_EMAILS: dict[DemoRole, str] = {
    "user": "demo@digest.local",
    "admin": "admin@digest.local",
}


def list_accounts() -> DemoAccountsResponse:
    _require_demo_mode()
    return DemoAccountsResponse(
        accounts=[
            DemoAccount(role=role, email=email) for role, email in DEMO_EMAILS.items()
        ]
    )


def login(role: DemoRole, repo: UserRepository) -> TokenResponse:
    _require_demo_mode()
    user = _get_or_create(role, repo)
    logger.info("demo login", user_id=str(user.id), role=role)
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=int(access_token_lifetime().total_seconds()),
    )


def _require_demo_mode() -> None:
    if not get_settings().demo_accounts:
        raise DemoModeDisabledError()


def _get_or_create(role: DemoRole, repo: UserRepository) -> User:
    email = DEMO_EMAILS[role]
    existing = repo.get_by_email(email)
    if existing is not None:
        return existing
    try:
        user = repo.create(
            User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                role=UserRole(role),
            )
        )
    except EmailAlreadyRegisteredError:
        # Two first clicks at once: the other request created it.
        return repo.get_by_email(email)
    repo.commit()
    logger.info("demo account created", user_id=str(user.id), role=role)
    return user
