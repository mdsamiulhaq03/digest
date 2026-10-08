from fastapi import APIRouter, Depends

from app.repositories.user_repository import UserRepository
from app.routers.dependencies import get_user_repository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service

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
