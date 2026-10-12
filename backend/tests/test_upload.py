import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.main import app
from app.models.document import Document
from app.models.job import Job, JobState
from app.routers.dependencies import get_job_queue
from tests.factories import CSV_BYTES, RecordingQueue, login_as
from tests.factories import upload as _upload

client = TestClient(app)


def test_upload_requires_a_token() -> None:
    assert _upload({}).status_code == 401


@pytest.mark.parametrize("filename", ["report.pdf", "script.py", "noextension", ""])
def test_unsupported_types_are_415_and_store_nothing(
    filename: str, as_some_user: None, upload_dir: Path, queue: RecordingQueue
) -> None:
    response = _upload({}, filename=filename)
    # An empty filename is rejected by multipart parsing itself, before us.
    assert response.status_code in (415, 422)
    assert list(upload_dir.iterdir()) == []
    assert queue.job_ids == []


def test_type_comes_from_the_extension_not_the_client_header(
    as_some_user: None, upload_dir: Path, queue: RecordingQueue
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("evil.exe", b"MZ...", "text/csv")},
    )
    assert response.status_code == 415


def test_oversized_upload_is_413_and_leaves_no_partial_file(
    as_some_user: None,
    upload_dir: Path,
    queue: RecordingQueue,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    response = _upload({}, body=b"x" * 11)
    assert response.status_code == 413
    assert "MB limit" in response.json()["error"]["message"]
    assert list(upload_dir.iterdir()) == []
    assert queue.job_ids == []


@pytest.mark.integration
def test_upload_is_accepted_stored_and_queued(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    response = _upload(sam.headers)

    assert response.status_code == 202
    body = response.json()
    assert (
        response.headers["Location"] == body["status_url"] == f"/jobs/{body['job_id']}"
    )
    assert queue.job_ids == [uuid.UUID(body["job_id"])]

    with SessionLocal() as session:
        document = session.get(Document, uuid.UUID(body["document_id"]))
        job = session.scalars(select(Job).where(Job.document_id == document.id)).one()
    assert document.text is None
    assert document.original_filename == "people.csv"
    assert document.content_type == "text/csv"
    assert document.size_bytes == len(CSV_BYTES)
    assert job.state == JobState.QUEUED
    assert job.attempts == 0
    assert (upload_dir / document.storage_key).read_bytes() == CSV_BYTES


@pytest.mark.integration
def test_uploaded_document_is_listed_without_insights_yet(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    _upload(sam.headers, filename="notes.txt", body=b"Hello there.")

    document = client.get("/documents", headers=sam.headers).json()["documents"][0]
    assert document["original_filename"] == "notes.txt"
    assert document["content_type"] == "text/plain"
    assert document["text"] is None
    assert document["insights"] is None
    assert document["csv_insights"] is None


@pytest.mark.integration
def test_two_users_same_filename_never_collide(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    alice = login_as("alice@example.com")
    bob = login_as("bob@example.com")
    first = _upload(alice.headers, body=b"a\n1\n").json()["document_id"]
    second = _upload(bob.headers, body=b"a\n2\n").json()["document_id"]

    assert (upload_dir / first).read_bytes() == b"a\n1\n"
    assert (upload_dir / second).read_bytes() == b"a\n2\n"


@pytest.mark.integration
def test_path_in_filename_is_never_used_on_disk(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    body = _upload(sam.headers, filename="..\\..\\etc\\people.csv").json()

    with SessionLocal() as session:
        document = session.get(Document, uuid.UUID(body["document_id"]))
    assert document.original_filename == "people.csv"
    assert document.storage_key == body["document_id"]
    assert [p.name for p in upload_dir.iterdir()] == [body["document_id"]]


@pytest.mark.integration
def test_redis_outage_still_accepts_the_upload(upload_dir: Path) -> None:
    app.dependency_overrides[get_job_queue] = lambda: RecordingQueue(fail=True)
    try:
        sam = login_as("sam@example.com")
        response = _upload(sam.headers)
    finally:
        app.dependency_overrides.pop(get_job_queue)

    # Stored and recorded as queued in Postgres; the sweeper will enqueue it.
    assert response.status_code == 202
    with SessionLocal() as session:
        job = session.get(Job, uuid.UUID(response.json()["job_id"]))
    assert job.state == JobState.QUEUED
