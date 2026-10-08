import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.job import Job


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
