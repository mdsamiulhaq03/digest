from fastapi import APIRouter, Depends

from app.repositories.user_repository import UserRepository
from app.routers.dependencies import get_user_repository, require_admin
from app.schemas.auth import UserListResponse
from app.services import user_service

# Guarded at the router, so a route added here later can't forget the check.
router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/users", response_model=UserListResponse)
def list_users(
    repo: UserRepository = Depends(get_user_repository),
) -> UserListResponse:
    return user_service.list_users(repo)
