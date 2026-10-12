import uuid
from dataclasses import asdict
from typing import NoReturn

from loguru import logger
from pydantic import BaseModel

from app.core.cache import JsonCache, document_key
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
    document_id: str, owner: User, repo: DocumentRepository, cache: JsonCache
) -> DocumentResponse:
    # A malformed id, a missing document and someone else's document are all
    # the same 404, so a caller can't probe ids to learn which documents exist.
    document_uuid = _parse_id(document_id)
    if document_uuid is None:
        _not_found(document_id)

    # The caller's identity was already checked against Postgres before we got
    # here, so a disabled or deleted user never reaches a cached entry.
    key = document_key(owner.id, document_uuid)
    cached = cache.get(key)
    if cached is not None:
        return DocumentResponse.model_validate(cached)

    document = repo.get_for_owner(document_uuid, owner.id)
    if document is None:
        _not_found(document_id)
    response = _to_response(document)
    if _is_complete(document):
        cache.set(key, response.model_dump(mode="json"))
    return response


def _is_complete(document: Document) -> bool:
    """Pasted text, or an upload whose job has stored its insights. Anything
    else is about to change, so caching it would only create staleness."""
    return document.text is not None or (
        document.insight is not None or document.csv_insight is not None
    )


def _parse_id(document_id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(document_id)
    except ValueError:
        return None


def _not_found(document_id: str) -> NoReturn:
    logger.info("document not found", document_id=document_id)
    raise DocumentNotFoundError(document_id)
