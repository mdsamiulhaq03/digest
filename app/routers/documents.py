from fastapi import APIRouter, Depends

from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.routers.dependencies import get_active_user, get_document_repository
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


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
