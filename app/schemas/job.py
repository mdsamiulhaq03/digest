import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Where a background job has got to. Poll until state is succeeded or
    failed; on success, the insights are on the document at document_url."""

    id: uuid.UUID
    document_id: uuid.UUID
    state: str = Field(..., description="queued | running | succeeded | failed")
    attempts: int
    last_error: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    document_url: str
