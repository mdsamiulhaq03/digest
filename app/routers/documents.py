from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.core.queue import JobQueue
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.routers.dependencies import (
    get_active_user,
    get_document_repository,
    get_job_queue,
    get_job_repository,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    UploadAcceptedResponse,
)
from app.services import document_service, upload_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(
    payload: DocumentCreate,
    user: User = Depends(get_active_user),
    repo: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    return document_service.create_document(payload, user, repo)


# BEFORE-MEASUREMENT VERSION (Phase 5, step 11): this is deliberately the
# common mistake - an `async def` handler doing blocking work (disk writes,
# database calls). Step 11 measures what that does to every other request,
# then fixes it.
@router.post("/upload", response_model=UploadAcceptedResponse, status_code=202)
async def upload_document(
    response: Response,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form(min_length=1, max_length=255)] = None,
    user: User = Depends(get_active_user),
    documents: DocumentRepository = Depends(get_document_repository),
    jobs: JobRepository = Depends(get_job_repository),
    queue: JobQueue = Depends(get_job_queue),
) -> UploadAcceptedResponse:
    accepted = upload_service.accept_upload(
        file.filename, file.file, title, user, documents, jobs, queue
    )
    response.headers["Location"] = accepted.status_url
    return accepted


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
