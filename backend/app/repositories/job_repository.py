import uuid
from datetime import datetime, timedelta

from sqlalchemy import ColumnElement, func, select, update
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

    # Every transition out of `running` names the attempt it belongs to. If the
    # sweeper has since taken the job back (or another worker has re-claimed
    # it), the attempt no longer matches, nothing changes, and the caller
    # learns it lost the job - so a slow worker can never overwrite a newer one.

    def mark_succeeded(self, job_id: uuid.UUID, attempt: int) -> bool:
        return self._finish(
            job_id, attempt, state=JobState.SUCCEEDED, finished_at=func.now()
        )

    def mark_failed(self, job_id: uuid.UUID, attempt: int, error: str) -> bool:
        return self._finish(
            job_id,
            attempt,
            state=JobState.FAILED,
            last_error=error,
            finished_at=func.now(),
        )

    def requeue(self, job_id: uuid.UUID, attempt: int, error: str) -> bool:
        return self._finish(
            job_id,
            attempt,
            state=JobState.QUEUED,
            last_error=error,
            started_at=None,
            queued_at=func.now(),
        )

    def _finish(self, job_id: uuid.UUID, attempt: int, **values: object) -> bool:
        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.state == JobState.RUNNING,
                Job.attempts == attempt,
            )
            .values(**values)
        )
        return self.db.execute(stmt).rowcount == 1

    # --- Sweeper side.

    def lock_stuck_running(self, older_than_seconds: int) -> list[Job]:
        """Running jobs whose worker has most likely died. Locked with SKIP
        LOCKED, so two sweepers never handle the same job."""
        stmt = (
            select(Job)
            .where(
                Job.state == JobState.RUNNING,
                Job.started_at < _seconds_ago(older_than_seconds),
            )
            .with_for_update(skip_locked=True)
        )
        return list(self.db.scalars(stmt))

    def find_unclaimed_queued(self, older_than_seconds: int) -> list[uuid.UUID]:
        """Queued jobs nobody has picked up - e.g. their enqueue was lost while
        Redis was down. Pushing one twice is harmless: only one claim wins."""
        stmt = select(Job.id).where(
            Job.state == JobState.QUEUED,
            Job.queued_at < _seconds_ago(older_than_seconds),
        )
        return list(self.db.scalars(stmt))


def _seconds_ago(seconds: int) -> ColumnElement[datetime]:
    # Measured on the database clock, the same clock that stamped the rows.
    return func.now() - timedelta(seconds=seconds)
