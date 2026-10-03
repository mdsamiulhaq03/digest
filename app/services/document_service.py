import uuid

from loguru import logger

from app.core.exceptions import DocumentNotFoundError
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
    logger.info("document created", document_id=str(created.id))
    return _to_response(created)


def list_documents(repo: DocumentRepository) -> DocumentListResponse:
    documents = repo.list_all()
    responses = [_to_response(document) for document in documents]
    return DocumentListResponse(documents=responses, total=len(responses))


def get_document(document_id: str, repo: DocumentRepository) -> DocumentResponse:
    try:
        document_uuid = uuid.UUID(document_id)
    except ValueError:
        logger.info("document not found", document_id=document_id)
        raise DocumentNotFoundError(document_id) from None

    document = repo.get_by_id(document_uuid)
    if document is None:
        logger.info("document not found", document_id=document_id)
        raise DocumentNotFoundError(document_id)
    return _to_response(document)
