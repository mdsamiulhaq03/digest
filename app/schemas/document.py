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


class DocumentResponse(BaseModel):
    """Response shape returned for a single document."""

    id: str
    title: str
    text: str
    insights: InsightsSchema
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Response shape returned for a list of documents."""

    documents: list[DocumentResponse]
    total: int
