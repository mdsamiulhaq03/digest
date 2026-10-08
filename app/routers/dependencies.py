"""FastAPI dependencies shared by more than one router.

The auth dependencies form a chain - each one takes the previous one as its
input and adds a single check:

    get_current_user  -> who is calling (token is valid, user still exists)
    get_active_user   -> ...and the account is not disabled
    require_admin     -> ...and the account is an admin

A route asks for the narrowest one it needs and receives a User, never a token.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import InvalidTokenError, PermissionDeniedError
from app.core.queue import JobQueue, get_redis
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository

# auto_error=False: a missing header comes back as None so it can be raised as
# our own 401 in the one error shape, instead of FastAPI's default response.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


# FastAPI resolves get_db once per request, so every repository in a request
# shares one session - which is what lets a service commit them together.
def get_job_repository(db: Session = Depends(get_db)) -> JobRepository:
    return JobRepository(db)


def get_job_queue() -> JobQueue:
    return JobQueue(get_redis())


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None:
        raise InvalidTokenError()

    user = repo.get_by_id(decode_access_token(credentials.credentials))
    if user is None:
        # Correctly signed, but the account has since been deleted. To the
        # caller that is no different from any other token that is no good.
        logger.info("token for deleted user rejected")
        raise InvalidTokenError()
    return user


def get_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        logger.info("inactive user rejected", user_id=str(user.id))
        raise PermissionDeniedError("Account is disabled")
    return user


def require_admin(user: User = Depends(get_active_user)) -> User:
    if user.role != UserRole.ADMIN:
        logger.info("non-admin rejected", user_id=str(user.id))
        raise PermissionDeniedError("Admin role required")
    return user
