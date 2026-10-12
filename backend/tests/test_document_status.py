"""A document's status - what a list needs to tell an upload still processing
from one that failed, which otherwise look the same (no insights yet)."""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.job_processor import process_job
from tests.factories import RecordingQueue, login_as, upload

client = TestClient(app)


def _listed(headers: dict[str, str]) -> dict[str, dict]:
    documents = client.get("/documents", headers=headers).json()["documents"]
    return {document["id"]: document for document in documents}


@pytest.mark.integration
def test_pasted_text_is_ready_and_has_no_job() -> None:
    sam = login_as("sam@example.com")
    created = client.post(
        "/documents", json={"title": "Notes", "text": "Hello."}, headers=sam.headers
    ).json()
    assert (created["status"], created["job_id"]) == ("ready", None)
    assert _listed(sam.headers)[created["id"]]["status"] == "ready"


@pytest.mark.integration
def test_an_upload_is_processing_until_its_job_succeeds(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(sam.headers).json()

    before = _listed(sam.headers)[accepted["document_id"]]
    assert before["status"] == "processing"
    assert before["job_id"] == accepted["job_id"]

    process_job(uuid.UUID(accepted["job_id"]), queue)
    after = client.get(f"/documents/{accepted['document_id']}", headers=sam.headers)
    assert after.json()["status"] == "ready"


@pytest.mark.integration
def test_an_upload_whose_job_gave_up_is_failed(
    upload_dir: Path, queue: RecordingQueue
) -> None:
    sam = login_as("sam@example.com")
    accepted = upload(
        sam.headers, filename="latin1.txt", body="café".encode("latin-1")
    ).json()

    process_job(uuid.UUID(accepted["job_id"]), queue)

    document = _listed(sam.headers)[accepted["document_id"]]
    assert document["status"] == "failed"
    assert document["insights"] is None
