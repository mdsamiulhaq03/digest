import uuid
from pathlib import PureWindowsPath
from typing import BinaryIO

from loguru import logger
from redis.exceptions import RedisError

from app.core import storage
from app.core.exceptions import UnsupportedFileTypeError
from app.core.queue import JobQueue
from app.models.document import Document
from app.models.job import Job
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.schemas.document import UploadAcceptedResponse

# The type is decided here from the extension, never taken from the client's
# Content-Type header, which is whatever the client chose to send.
CONTENT_TYPES = {".txt": "text/plain", ".csv": "text/csv"}
MAX_FILENAME_LENGTH = 255


def accept_upload(
    filename: str | None,
    source: BinaryIO,
    title: str | None,
    owner: User,
    documents: DocumentRepository,
    jobs: JobRepository,
    queue: JobQueue,
) -> UploadAcceptedResponse:
    display_name = _display_name(filename)
    content_type = _content_type(display_name)

    document_id = uuid.uuid4()
    storage_key = str(document_id)
    size_bytes = storage.save(source, storage_key)

    try:
        documents.create(
            Document(
                id=document_id,
                owner_id=owner.id,
                title=title or display_name,
                original_filename=display_name,
                storage_key=storage_key,
                size_bytes=size_bytes,
                content_type=content_type,
            )
        )
        job = jobs.create(Job(document_id=document_id))
        # Both repositories share the request's session: one commit, so a
        # document never exists without its job, or a job without its document.
        jobs.commit()
    except Exception:
        storage.delete(storage_key)
        raise

    _enqueue(queue, job.id)
    logger.info(
        "upload accepted",
        document_id=str(document_id),
        job_id=str(job.id),
        size_bytes=size_bytes,
    )
    return UploadAcceptedResponse(
        document_id=document_id, job_id=job.id, status_url=f"/jobs/{job.id}"
    )


def _display_name(filename: str | None) -> str:
    # PureWindowsPath splits on both "/" and "\", so "C:\fakepath\a.csv" and
    # "../../a.csv" both come down to "a.csv". It is only ever displayed.
    name = PureWindowsPath(filename or "").name
    return name[:MAX_FILENAME_LENGTH]


def _content_type(filename: str) -> str:
    suffix = PureWindowsPath(filename).suffix.lower()
    if suffix not in CONTENT_TYPES:
        raise UnsupportedFileTypeError(sorted(CONTENT_TYPES))
    return CONTENT_TYPES[suffix]


def _enqueue(queue: JobQueue, job_id: uuid.UUID) -> None:
    # The job is already committed as queued, so the upload has succeeded
    # either way. If Redis is down, the sweeper finds the job in Postgres and
    # queues it later - failing the request now would only make the client
    # retry an upload that is already safely stored.
    try:
        queue.enqueue(job_id)
    except RedisError:
        logger.warning("enqueue failed, sweeper will retry", job_id=str(job_id))
