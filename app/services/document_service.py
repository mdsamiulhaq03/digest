import uuid
from dataclasses import asdict

from loguru import logger
from pydantic import BaseModel

from app.core.exceptions import DocumentNotFoundError
from app.models.document import Document
from app.models.insight import Insight
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    CsvInsightsSchema,
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    InsightsSchema,
)
from app.utils.insights import compute_insights


def _to_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        text=document.text,
        original_filename=document.original_filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        insights=_validated(InsightsSchema, document.insight),
        csv_insights=_validated(CsvInsightsSchema, document.csv_insight),
        created_at=document.created_at,
    )


def _validated[S: BaseModel](schema: type[S], row: object | None) -> S | None:
    return None if row is None else schema.model_validate(row, from_attributes=True)


def create_document(
    payload: DocumentCreate, owner: User, repo: DocumentRepository
) -> DocumentResponse:
    document = Document(title=payload.title, text=payload.text, owner_id=owner.id)
    document.insight = Insight(**asdict(compute_insights(payload.text)))
    created = repo.create(document)
    repo.commit()
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
