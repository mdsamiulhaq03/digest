from fastapi import APIRouter, Depends

from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.routers.dependencies import get_active_user, get_job_repository
from app.schemas.job import JobResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    user: User = Depends(get_active_user),
    repo: JobRepository = Depends(get_job_repository),
) -> JobResponse:
    return job_service.get_job(job_id, user, repo)
