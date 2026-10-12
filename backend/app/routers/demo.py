from fastapi import APIRouter, Depends

from app.repositories.user_repository import UserRepository
from app.routers.dependencies import get_user_repository
from app.schemas.auth import TokenResponse
from app.schemas.demo import DemoAccountsResponse, DemoLoginRequest
from app.services import demo_service

# Both routes answer 404 unless DEMO_ACCOUNTS is on.
router = APIRouter(prefix="/auth/demo", tags=["auth"])


@router.get("", response_model=DemoAccountsResponse)
def list_demo_accounts() -> DemoAccountsResponse:
    return demo_service.list_accounts()


@router.post("/login", response_model=TokenResponse)
def demo_login(
    payload: DemoLoginRequest,
    repo: UserRepository = Depends(get_user_repository),
) -> TokenResponse:
    return demo_service.login(payload.role, repo)
