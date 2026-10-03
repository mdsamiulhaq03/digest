from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(
    payload: DocumentCreate,
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    return document_service.create_document(payload, repo)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentListResponse:
    return document_service.list_documents(repo)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    document = document_service.get_document(document_id, repo)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
