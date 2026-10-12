"""Turns one queued job into stored insights. Business logic only: it never
knows whether it was called from the worker loop or a test."""

import csv
import uuid
from collections.abc import Callable

from loguru import logger
from sqlalchemy.orm import Session

from app.core import storage
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.queue import JobQueue
from app.models.document import Document
from app.repositories.insight_repository import InsightRepository
from app.repositories.job_repository import JobRepository
from app.utils.csv_insights import compute_csv_insights
from app.utils.insights import compute_insights

UNEXPECTED_ERROR = "Unexpected error while processing the file"


class PermanentJobError(Exception):
    """A failure that no retry can fix. The message is shown to the client as
    last_error, so it must say what is wrong without exposing internals."""


def process_job(
    job_id: uuid.UUID,
    queue: JobQueue,
    session_factory: Callable[[], Session] = SessionLocal,
) -> None:
    # A fresh session per job: a worker holding one session for its whole
    # life would carry stale state and a long-open transaction between jobs.
    with session_factory() as db:
        jobs = JobRepository(db)
        job = jobs.claim(job_id)
        if job is None:
            # Already running, finished, or gone - e.g. the same id was
            # queued twice. Only one claim can ever win.
            logger.info("job not claimable, skipped", job_id=str(job_id))
            return
        jobs.commit()
        # Captured now: after a rollback the session would reload `attempts`
        # from the database, and it may no longer be ours.
        attempt = job.attempts
        logger.info("job started", job_id=str(job_id), attempt=attempt)

        try:
            _compute_and_store(jobs.document_for(job), InsightRepository(db))
        except Exception as exc:  # noqa: BLE001 - every failure must be recorded
            db.rollback()
            _record_failure(jobs, job_id, attempt, exc, queue)
            return

        # Insights and the success mark land in one commit: a job is never
        # "succeeded" without its results, nor results left on a job that
        # still looks unfinished.
        if jobs.mark_succeeded(job_id, attempt):
            jobs.commit()
            logger.info("job succeeded", job_id=str(job_id))
        else:
            db.rollback()
            logger.warning("job claim lost before finishing", job_id=str(job_id))


def _compute_and_store(document: Document, insights: InsightRepository) -> None:
    text = _read_text(document)
    try:
        if document.content_type == "text/csv":
            insights.save_csv(document.id, compute_csv_insights(text))
        else:
            insights.save_text(document.id, compute_insights(text))
    except csv.Error as exc:
        raise PermanentJobError("File could not be parsed as CSV") from exc


def _read_text(document: Document) -> str:
    try:
        raw = storage.path_for(document.storage_key).read_bytes()
    except FileNotFoundError as exc:
        raise PermanentJobError("Uploaded file is missing") from exc
    try:
        # utf-8-sig also strips the byte-order mark spreadsheet tools add.
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PermanentJobError("File is not valid UTF-8") from exc


def _record_failure(
    jobs: JobRepository,
    job_id: uuid.UUID,
    attempt: int,
    exc: Exception,
    queue: JobQueue,
) -> None:
    permanent = isinstance(exc, PermanentJobError)
    message = str(exc) if permanent else UNEXPECTED_ERROR
    # The traceback is for the logs; the client only ever sees `message`.
    logger.opt(exception=exc).warning(
        "job attempt failed", job_id=str(job_id), attempt=attempt
    )

    give_up = permanent or attempt >= get_settings().job_max_attempts
    if give_up:
        recorded = jobs.mark_failed(job_id, attempt, message)
    else:
        recorded = jobs.requeue(job_id, attempt, message)
    jobs.commit()

    if not recorded:
        logger.warning("job claim lost before failing", job_id=str(job_id))
    elif give_up:
        logger.warning("job failed", job_id=str(job_id), attempts=attempt)
    else:
        queue.try_enqueue(job_id)
