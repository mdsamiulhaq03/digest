import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    InsightsSchema,
)
from app.utils.insights import compute_insights

router = APIRouter(prefix="/documents", tags=["documents"])

_documents: dict[str, DocumentResponse] = {}


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(payload: DocumentCreate) -> DocumentResponse:
    insights = InsightsSchema(**compute_insights(payload.text))
    document = DocumentResponse(
        id=str(uuid.uuid4()),
        title=payload.title,
        text=payload.text,
        insights=insights,
        created_at=datetime.now(timezone.utc),
    )
    _documents[document.id] = document
    return document


@router.get("", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    documents = list(_documents.values())
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str) -> DocumentResponse:
    document = _documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
