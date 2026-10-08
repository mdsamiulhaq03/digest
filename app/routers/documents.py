from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.routers.dependencies import get_active_user
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(
    payload: DocumentCreate,
    user: User = Depends(get_active_user),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    return document_service.create_document(payload, user, repo)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    user: User = Depends(get_active_user),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentListResponse:
    return document_service.list_documents(user, repo)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    user: User = Depends(get_active_user),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    return document_service.get_document(document_id, user, repo)
