import uuid

from app.models.document import Document
from app.models.insight import Insight
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    InsightsSchema,
)
from app.utils.insights import compute_insights


def _to_response(document: Document) -> DocumentResponse:
    insights = InsightsSchema.model_validate(document.insight, from_attributes=True)
    return DocumentResponse(
        id=document.id,
        title=document.title,
        text=document.text,
        insights=insights,
        created_at=document.created_at,
    )


def create_document(
    payload: DocumentCreate, repo: DocumentRepository
) -> DocumentResponse:
    insight_data = compute_insights(payload.text)
    document = Document(title=payload.title, text=payload.text)
    document.insight = Insight(**insight_data)
    created = repo.create(document)
    return _to_response(created)


def list_documents(repo: DocumentRepository) -> DocumentListResponse:
    documents = repo.list_all()
    responses = [_to_response(document) for document in documents]
    return DocumentListResponse(documents=responses, total=len(responses))


def get_document(document_id: str, repo: DocumentRepository) -> DocumentResponse | None:
    try:
        document_uuid = uuid.UUID(document_id)
    except ValueError:
        return None

    document = repo.get_by_id(document_uuid)
    if document is None:
        return None
    return _to_response(document)
