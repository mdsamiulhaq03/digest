from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import (
    create_access_token,
    hash_password,
    spend_password_check,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


def _normalize_email(email: str) -> str:
    # The database refuses mixed case (ck_users_email_lowercase); normalising
    # here means "Sam@x.com" logs in to the account "sam@x.com" registered.
    return email.strip().lower()


def register(payload: RegisterRequest, repo: UserRepository) -> UserResponse:
    email = _normalize_email(payload.email)
    if repo.get_by_email(email) is not None:
        raise EmailAlreadyRegisteredError()

    user = repo.create(User(email=email, password_hash=hash_password(payload.password)))
    logger.info("user registered", user_id=str(user.id))
    return UserResponse.model_validate(user)


def login(payload: LoginRequest, repo: UserRepository) -> TokenResponse:
    user = repo.get_by_email(_normalize_email(payload.email))
    if user is None:
        # Hash anyway, so an unknown email takes as long as a wrong password
        # and response time can't be used to find out who has an account.
        spend_password_check(payload.password)
        logger.info("login failed", reason="unknown_email")
        raise InvalidCredentialsError()

    if not verify_password(user.password_hash, payload.password):
        logger.info("login failed", reason="wrong_password", user_id=str(user.id))
        raise InvalidCredentialsError()

    # Checked after the password, so only someone who already knows it can
    # learn the account is disabled - and even then the message is the same.
    if not user.is_active:
        logger.info("login failed", reason="inactive", user_id=str(user.id))
        raise InvalidCredentialsError()

    logger.info("user logged in", user_id=str(user.id))
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=get_settings().access_token_expire_minutes * 60,
    )
