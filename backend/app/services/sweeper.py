"""Recovers jobs that Redis alone would lose. Postgres is the source of truth,
so anything stuck can be found there and put back in motion."""

from collections.abc import Callable
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.queue import JobQueue
from app.repositories.job_repository import JobRepository

STOPPED_MID_JOB = "Worker stopped while processing the file"


@dataclass(frozen=True)
class SweepResult:
    requeued: int
    failed: int
    re_enqueued: int


def sweep(
    queue: JobQueue, session_factory: Callable[[], Session] = SessionLocal
) -> SweepResult:
    settings = get_settings()
    with session_factory() as db:
        jobs = JobRepository(db)

        # A running job past the timeout means its worker died mid-job (or was
        # killed). Its attempt was counted at claim time, so this is just the
        # normal retry rule: back to queued, or failed once attempts run out.
        requeued, failed = [], []
        for job in jobs.lock_stuck_running(settings.job_stuck_after_seconds):
            if job.attempts >= settings.job_max_attempts:
                jobs.mark_failed(job.id, job.attempts, STOPPED_MID_JOB)
                failed = [*failed, job.id]
            else:
                jobs.requeue(job.id, job.attempts, STOPPED_MID_JOB)
                requeued = [*requeued, job.id]

        unclaimed = jobs.find_unclaimed_queued(settings.job_stuck_after_seconds)
        jobs.commit()

    # Pushed only after the commit, so a worker can never pop an id whose
    # state change it can't yet see.
    to_enqueue = [*requeued, *unclaimed]
    for job_id in to_enqueue:
        queue.try_enqueue(job_id)

    result = SweepResult(
        requeued=len(requeued), failed=len(failed), re_enqueued=len(unclaimed)
    )
    if requeued or failed or unclaimed:
        logger.warning("sweeper recovered jobs", **vars(result))
    return result
