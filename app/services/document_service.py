import uuid
from dataclasses import asdict

from loguru import logger

from app.core.exceptions import DocumentNotFoundError
from app.models.document import Document
from app.models.insight import Insight
from app.models.user import User
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
    payload: DocumentCreate, owner: User, repo: DocumentRepository
) -> DocumentResponse:
    document = Document(title=payload.title, text=payload.text, owner_id=owner.id)
    document.insight = Insight(**asdict(compute_insights(payload.text)))
    created = repo.create(document)
    logger.info("document created", document_id=str(created.id), owner_id=str(owner.id))
    return _to_response(created)


def list_documents(owner: User, repo: DocumentRepository) -> DocumentListResponse:
    documents = repo.list_for_owner(owner.id)
    responses = [_to_response(document) for document in documents]
    return DocumentListResponse(documents=responses, total=len(responses))


def get_document(
    document_id: str, owner: User, repo: DocumentRepository
) -> DocumentResponse:
    # A malformed id, a missing document and someone else's document are all
    # the same 404, so a caller can't probe ids to learn which documents exist.
    document = _find_owned_document(document_id, owner, repo)
    if document is None:
        logger.info("document not found", document_id=document_id)
        raise DocumentNotFoundError(document_id)
    return _to_response(document)


def _find_owned_document(
    document_id: str, owner: User, repo: DocumentRepository
) -> Document | None:
    try:
        document_uuid = uuid.UUID(document_id)
    except ValueError:
        return None
    return repo.get_for_owner(document_uuid, owner.id)
