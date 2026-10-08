import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.job import Job, JobState


class JobRepository:
    """Stages changes but never commits: the service decides where a unit of
    work ends, so several writes can succeed or fail together."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, job: Job) -> Job:
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def commit(self) -> None:
        self.db.commit()

    def get_for_owner(self, job_id: uuid.UUID, owner_id: uuid.UUID) -> Job | None:
        # A job belongs to whoever owns its document; the join puts that
        # ownership rule inside the query, as for documents themselves.
        stmt = (
            select(Job)
            .join(Document, Job.document_id == Document.id)
            .where(Job.id == job_id, Document.owner_id == owner_id)
        )
        return self.db.scalars(stmt).first()

    # --- Worker side. Each state change is one conditional UPDATE, so two
    # workers can never both believe they own a job.

    def claim(self, job_id: uuid.UUID) -> Job | None:
        """Move a queued job to running and count the attempt. Returns None if
        the job isn't queued (already claimed, finished, or deleted)."""
        stmt = (
            update(Job)
            .where(Job.id == job_id, Job.state == JobState.QUEUED)
            .values(
                state=JobState.RUNNING,
                attempts=Job.attempts + 1,
                started_at=func.now(),
            )
            .returning(Job)
        )
        return self.db.scalars(stmt).first()

    def document_for(self, job: Job) -> Document:
        # Not owner-scoped: the worker acts for the system, not for a caller.
        # Reached only through a job the worker has just claimed.
        return self.db.get_one(Document, job.document_id)

    def mark_succeeded(self, job_id: uuid.UUID) -> None:
        self._set(job_id, state=JobState.SUCCEEDED, finished_at=func.now())

    def mark_failed(self, job_id: uuid.UUID, error: str) -> None:
        self._set(
            job_id, state=JobState.FAILED, last_error=error, finished_at=func.now()
        )

    def requeue(self, job_id: uuid.UUID, error: str) -> None:
        self._set(job_id, state=JobState.QUEUED, last_error=error, started_at=None)

    def _set(self, job_id: uuid.UUID, **values: object) -> None:
        self.db.execute(update(Job).where(Job.id == job_id).values(**values))
