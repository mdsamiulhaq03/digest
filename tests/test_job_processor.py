"""The job processor against real Postgres and real files (in a temp folder),
with Redis swapped for a recording queue."""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.core.db import SessionLocal
from app.main import app
from app.models.csv_insight import CsvInsight
from app.models.insight import Insight
from app.models.job import Job, JobState
from app.services import job_processor
from app.services.job_processor import UNEXPECTED_ERROR, process_job
from tests.factories import RecordingQueue, login_as, upload

pytestmark = pytest.mark.integration


def _uploaded_job(filename: str, body: bytes) -> tuple[uuid.UUID, uuid.UUID]:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers, filename=filename, body=body).json()
    return uuid.UUID(accepted["job_id"]), uuid.UUID(accepted["document_id"])


def _job(job_id: uuid.UUID) -> Job:
    with SessionLocal() as session:
        return session.get_one(Job, job_id)


def _count(model: type) -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_csv_job_stores_csv_insights_and_succeeds(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id, document_id = _uploaded_job("people.csv", b"name,age\nada,36\nalan,41\n")
    process_job(job_id, queue)

    job = _job(job_id)
    assert job.state == JobState.SUCCEEDED
    assert job.attempts == 1
    assert job.started_at is not None
    assert job.finished_at is not None
    with SessionLocal() as session:
        insights = session.get_one(CsvInsight, document_id)
    assert insights.row_count == 2
    assert insights.columns[1]["name"] == "age"
    assert insights.columns[1]["mean"] == 38.5


def test_text_job_stores_text_insights(upload_dir: Path, queue: RecordingQueue) -> None:
    job_id, document_id = _uploaded_job("notes.txt", b"Hello world. Hello again!")
    process_job(job_id, queue)

    assert _job(job_id).state == JobState.SUCCEEDED
    with SessionLocal() as session:
        assert session.get_one(Insight, document_id).word_count == 4


def test_result_is_visible_through_the_api(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    client = TestClient(app)
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()
    process_job(uuid.UUID(accepted["job_id"]), queue)

    job = client.get(accepted["status_url"], headers=sam.headers).json()
    document = client.get(job["document_url"], headers=sam.headers).json()
    assert job["state"] == "succeeded"
    assert document["csv_insights"]["row_count"] == 2
    assert document["insights"] is None


def test_invalid_utf8_fails_at_once_without_retry(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id, _ = _uploaded_job("bad.txt", b"caf\xe9 au lait")  # latin-1, not UTF-8
    process_job(job_id, queue)

    job = _job(job_id)
    assert job.state == JobState.FAILED
    assert job.attempts == 1
    assert job.last_error == "File is not valid UTF-8"
    assert queue.job_ids == [job_id]  # only the original enqueue, no retry


def test_missing_file_fails_at_once(upload_dir: Path, queue: RecordingQueue) -> None:
    job_id, document_id = _uploaded_job("people.csv", b"a\n1\n")
    (upload_dir / str(document_id)).unlink()
    process_job(job_id, queue)

    job = _job(job_id)
    assert job.state == JobState.FAILED
    assert job.last_error == "Uploaded file is missing"


def test_unexpected_error_is_retried_then_fails_after_three_attempts(
    upload_dir: Path, queue: RecordingQueue, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(text: str) -> None:
        raise RuntimeError("secret internal detail: /etc/passwd")

    monkeypatch.setattr(job_processor, "compute_csv_insights", explode)
    job_id, _ = _uploaded_job("people.csv", b"a\n1\n")

    process_job(job_id, queue)
    job = _job(job_id)
    assert (job.state, job.attempts) == (JobState.QUEUED, 1)
    assert job.started_at is None
    assert job.last_error == UNEXPECTED_ERROR

    process_job(job_id, queue)
    process_job(job_id, queue)
    job = _job(job_id)
    assert (job.state, job.attempts) == (JobState.FAILED, 3)
    assert job.finished_at is not None
    # The exception text is for the logs, never for last_error.
    assert "secret" not in job.last_error
    # Enqueued on upload, then re-enqueued after attempts 1 and 2 only.
    assert queue.job_ids == [job_id, job_id, job_id]
    assert _count(CsvInsight) == 0


def test_a_job_is_only_ever_claimed_once(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id, _ = _uploaded_job("people.csv", b"a\n1\n")
    process_job(job_id, queue)
    process_job(job_id, queue)  # the same id delivered twice

    job = _job(job_id)
    assert (job.state, job.attempts) == (JobState.SUCCEEDED, 1)


def test_rerunning_a_job_replaces_insights_instead_of_duplicating(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    job_id, _ = _uploaded_job("people.csv", b"a\n1\n2\n")
    process_job(job_id, queue)
    # Simulate a crash after the insights were written but before the job was
    # marked done: put it back to queued and run it again.
    with SessionLocal() as session:
        session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(state=JobState.QUEUED, finished_at=None)
        )
        session.commit()
    process_job(job_id, queue)

    assert _job(job_id).state == JobState.SUCCEEDED
    assert _count(CsvInsight) == 1


def test_unknown_job_id_is_skipped(queue: RecordingQueue) -> None:
    process_job(uuid.uuid4(), queue)  # must not raise
