import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Request body for creating a new document."""

    title: str = Field(..., min_length=1, max_length=255)
    text: str = Field(..., min_length=1)


class InsightsSchema(BaseModel):
    """Computed text insights returned to the client."""

    char_count: int
    char_count_no_whitespace: int
    word_count: int
    unique_word_count: int
    sentence_count: int
    paragraph_count: int
    average_word_length: float
    top_words: list[str]
    estimated_reading_time_seconds: float


class ColumnStatsSchema(BaseModel):
    """Per-column statistics for an uploaded CSV."""

    name: str
    null_count: int
    inferred_type: str
    min: float | None
    max: float | None
    mean: float | None


class CsvInsightsSchema(BaseModel):
    """Computed CSV insights returned to the client."""

    row_count: int
    column_count: int
    columns: list[ColumnStatsSchema]


class DocumentResponse(BaseModel):
    """Response shape returned for a single document.

    Pasted text has `text` and `insights`. An uploaded file has the file fields,
    and `insights` (.txt) or `csv_insights` (.csv) once its job has succeeded -
    until then, both are null."""

    id: uuid.UUID
    title: str
    text: str | None
    original_filename: str | None
    content_type: str | None
    size_bytes: int | None
    insights: InsightsSchema | None
    csv_insights: CsvInsightsSchema | None
    created_at: datetime


class UploadAcceptedResponse(BaseModel):
    """Returned with 202: the file is stored, its insights are not computed yet."""

    document_id: uuid.UUID
    job_id: uuid.UUID
    status_url: str


class DocumentListResponse(BaseModel):
    """Response shape returned for a list of documents."""

    documents: list[DocumentResponse]
    total: int
