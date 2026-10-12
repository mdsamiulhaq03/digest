from fastapi import APIRouter, Depends

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.routers.dependencies import get_active_user, get_user_repository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    payload: RegisterRequest,
    repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    return auth_service.register(payload, repo)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    return auth_service.login(payload, repo)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_active_user)) -> UserResponse:
    """Who the token belongs to. Also how a client checks a stored token is
    still good: expired or for a deleted user is 401, disabled is 403."""
    return user_service.describe(user)
