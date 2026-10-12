import uuid

from loguru import logger

from app.core.exceptions import JobNotFoundError
from app.models.job import Job
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobResponse


def get_job(job_id: str, owner: User, repo: JobRepository) -> JobResponse:
    # Same rule as documents: malformed, missing and someone else's are all
    # one 404, so job ids can't be probed.
    job = _find_owned_job(job_id, owner, repo)
    if job is None:
        logger.info("job not found", job_id=job_id)
        raise JobNotFoundError(job_id)
    return _to_response(job)


def _find_owned_job(job_id: str, owner: User, repo: JobRepository) -> Job | None:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        return None
    return repo.get_for_owner(job_uuid, owner.id)


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        document_id=job.document_id,
        state=job.state,
        attempts=job.attempts,
        last_error=job.last_error,
        queued_at=job.queued_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        document_url=f"/documents/{job.document_id}",
    )
