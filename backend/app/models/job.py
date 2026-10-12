import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class JobState(StrEnum):
    """queued -> running -> succeeded | failed. A failed attempt goes back to
    queued until the attempt limit, then stays failed."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_jobs_document_id"),
        CheckConstraint(
            "state IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_jobs_state",
        ),
        CheckConstraint("attempts >= 0", name="ck_jobs_attempts_non_negative"),
        # A job has a finish time exactly when it has finished.
        CheckConstraint(
            "(state IN ('succeeded', 'failed')) = (finished_at IS NOT NULL)",
            name="ck_jobs_finished_at",
        ),
        # The sweeper only ever looks for running jobs, a small set at any moment.
        Index(
            "ix_jobs_running_started_at",
            "started_at",
            postgresql_where=text("state = 'running'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # One job per document; a retry reuses the same row.
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id", ondelete="CASCADE", name="fk_jobs_document_id_documents"
        ),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=JobState.QUEUED.value
    )
    attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    # Kept after a later success, so the history of what went wrong survives.
    last_error: Mapped[str | None] = mapped_column(Text)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
