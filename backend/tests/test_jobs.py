import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.models.job import Job, JobState
from tests.factories import RecordingQueue, login_as, upload

client = TestClient(app)


def test_job_status_requires_a_token() -> None:
    assert client.get(f"/jobs/{uuid.uuid4()}").status_code == 401


def test_malformed_job_id_is_404(as_some_user: None) -> None:
    response = client.get("/jobs/not-a-uuid")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not-a-uuid not found"


@pytest.mark.integration
def test_new_upload_reports_queued(upload_dir: Path, queue: RecordingQueue) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()

    response = client.get(accepted["status_url"], headers=sam.headers)
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == accepted["job_id"]
    assert job["state"] == "queued"
    assert job["attempts"] == 0
    assert job["last_error"] is None
    assert job["started_at"] is None
    assert job["finished_at"] is None
    assert job["document_url"] == f"/documents/{accepted['document_id']}"


@pytest.mark.integration
def test_status_reflects_what_the_worker_recorded(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()
    now = datetime.now(UTC)
    with SessionLocal() as session:
        session.execute(
            update(Job)
            .where(Job.id == uuid.UUID(accepted["job_id"]))
            .values(
                state=JobState.FAILED,
                attempts=3,
                last_error="File is not valid UTF-8",
                started_at=now,
                finished_at=now,
            )
        )
        session.commit()

    job = client.get(accepted["status_url"], headers=sam.headers).json()
    assert job["state"] == "failed"
    assert job["attempts"] == 3
    assert job["last_error"] == "File is not valid UTF-8"
    assert job["finished_at"] is not None


@pytest.mark.integration
def test_another_users_job_is_a_404(upload_dir: Path, queue: RecordingQueue) -> None:
    alice = login_as("alice@example.com")
    bob = login_as("bob@example.com")
    status_url = upload(alice.headers).json()["status_url"]

    assert client.get(status_url, headers=bob.headers).status_code == 404
    assert client.get(status_url, headers=alice.headers).status_code == 200


@pytest.mark.integration
def test_unknown_job_is_a_404() -> None:
    sam = login_as("sam@example.com")
    response = client.get(f"/jobs/{uuid.uuid4()}", headers=sam.headers)
    assert response.status_code == 404
