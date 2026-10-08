from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserListResponse, UserResponse


def list_users(repo: UserRepository) -> UserListResponse:
    users = [UserResponse.model_validate(user) for user in repo.list_all()]
    return UserListResponse(users=users, total=len(users))
