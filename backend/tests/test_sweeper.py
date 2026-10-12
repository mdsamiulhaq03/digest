import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import update

from app.core.db import SessionLocal
from app.models.job import Job, JobState
from app.repositories.job_repository import JobRepository
from app.services.sweeper import STOPPED_MID_JOB, sweep
from tests.factories import RecordingQueue, login_as, upload

pytestmark = pytest.mark.integration

LONG_AGO = datetime.now(UTC) - timedelta(hours=1)


def _job_in_state(**values: object) -> uuid.UUID:
    """An uploaded job, forced into whatever state the test needs."""
    sam = login_as(f"{uuid.uuid4().hex}@example.com")
    job_id = uuid.UUID(upload(sam.headers).json()["job_id"])
    if values:
        with SessionLocal() as session:
            session.execute(update(Job).where(Job.id == job_id).values(**values))
            session.commit()
    return job_id


def _job(job_id: uuid.UUID) -> Job:
    with SessionLocal() as session:
        return session.get_one(Job, job_id)


def test_job_left_running_by_a_dead_worker_is_requeued(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id = _job_in_state(state=JobState.RUNNING, attempts=1, started_at=LONG_AGO)
    queue.job_ids = []

    result = sweep(queue)

    job = _job(job_id)
    assert (job.state, job.attempts) == (JobState.QUEUED, 1)
    assert job.started_at is None
    assert job.last_error == STOPPED_MID_JOB
    assert queue.job_ids == [job_id]
    assert result.requeued == 1


def test_stuck_job_on_its_last_attempt_fails(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id = _job_in_state(state=JobState.RUNNING, attempts=3, started_at=LONG_AGO)
    queue.job_ids = []

    result = sweep(queue)

    job = _job(job_id)
    assert job.state == JobState.FAILED
    assert job.finished_at is not None
    assert queue.job_ids == []
    assert result.failed == 1


def test_recently_started_job_is_left_alone(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id = _job_in_state(
        state=JobState.RUNNING, attempts=1, started_at=datetime.now(UTC)
    )
    sweep(queue)
    assert _job(job_id).state == JobState.RUNNING


def test_queued_job_that_never_reached_redis_is_pushed_again(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id = _job_in_state(queued_at=LONG_AGO)
    queue.job_ids = []  # as if the upload's push had been lost

    result = sweep(queue)

    assert queue.job_ids == [job_id]
    assert _job(job_id).state == JobState.QUEUED
    assert result.re_enqueued == 1


def test_fresh_queued_job_is_not_pushed_twice(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    _job_in_state()
    queue.job_ids = []
    sweep(queue)
    assert queue.job_ids == []


def test_slow_worker_cannot_overwrite_after_losing_its_claim(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    # Worker A claims attempt 1, then stalls past the timeout. The sweeper
    # requeues the job and worker B claims attempt 2. When A finally finishes,
    # its write must not land.
    job_id = _job_in_state(state=JobState.RUNNING, attempts=1, started_at=LONG_AGO)
    sweep(queue)
    with SessionLocal() as session:
        JobRepository(session).claim(job_id)  # worker B: attempt 2
        session.commit()

    with SessionLocal() as session:
        lost = not JobRepository(session).mark_succeeded(job_id, attempt=1)
        session.commit()

    assert lost
    job = _job(job_id)
    assert (job.state, job.attempts) == (JobState.RUNNING, 2)
