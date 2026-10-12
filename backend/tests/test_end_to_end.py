"""An upload's whole journey, with nothing faked on the way.

Register and log in through the API, upload, and the job id travels through
the real Redis list to the real worker loop, which writes the insights to
Postgres; the test then polls the API until the job finishes, the way a client
would. The worker runs in a thread here rather than its own container, so the
only things CI has to provide are Postgres and Redis.
"""

import threading
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import redis
from fastapi.testclient import TestClient

from app import worker
from app.core.queue import JobQueue, connect
from app.main import app
from app.services import job_processor

client = TestClient(app)

PASSWORD = "correct-horse-battery"
JOB_DEADLINE_SECONDS = 15
POLL_INTERVAL_SECONDS = 0.05
FINISHED = {"succeeded", "failed"}

# Hand-countable: 9 words, 3 sentences, 2 paragraphs; "the" and "a" are
# stopwords, "fox" is the only repeat.
TEXT = "The fox ran. The fox hid.\n\nA bird sang."
CSV = b"name,age\nada,36\nalan,41\n"


@pytest.fixture
def running_worker(
    real_redis: redis.Redis, upload_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    # The loop notices a stop between waits on Redis; a short wait keeps
    # shutting it down at the end of each test quick.
    monkeypatch.setattr(worker, "POLL_SECONDS", 1)
    stop = threading.Event()
    queue = JobQueue(connect(worker.SOCKET_TIMEOUT_SECONDS))
    thread = threading.Thread(target=worker.run_loop, args=(queue, stop))
    thread.start()
    yield
    stop.set()
    thread.join(timeout=10)
    assert not thread.is_alive(), "worker did not stop"


def _register_and_log_in() -> dict[str, str]:
    email = f"{uuid.uuid4().hex}@example.com"
    credentials = {"email": email, "password": PASSWORD}
    assert client.post("/auth/register", json=credentials).status_code == 201
    login = client.post("/auth/login", json=credentials)
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _upload(headers: dict[str, str], filename: str, body: bytes) -> dict:
    response = client.post(
        "/documents/upload", files={"file": (filename, body)}, headers=headers
    )
    assert response.status_code == 202
    accepted = response.json()
    assert response.headers["Location"] == accepted["status_url"]
    return accepted


def _wait_until_finished(status_url: str, headers: dict[str, str]) -> dict:
    """Poll like a client would, up to a deadline - never a fixed sleep that
    is either too short on a slow CI runner or wasted on a fast one."""
    deadline = time.monotonic() + JOB_DEADLINE_SECONDS
    while True:
        job = client.get(status_url, headers=headers).json()
        if job["state"] in FINISHED:
            return job
        if time.monotonic() > deadline:
            pytest.fail(f"job not finished after {JOB_DEADLINE_SECONDS}s: {job}")
        time.sleep(POLL_INTERVAL_SECONDS)


def _document(url: str, headers: dict[str, str]) -> dict:
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    return response.json()


@pytest.mark.integration
def test_text_upload_goes_through_queue_and_worker_to_stored_insights(
    running_worker: None,
) -> None:
    headers = _register_and_log_in()
    accepted = _upload(headers, "fox.txt", TEXT.encode())

    job = _wait_until_finished(accepted["status_url"], headers)

    assert job["state"] == "succeeded"
    assert job["attempts"] == 1
    assert job["last_error"] is None
    document = _document(job["document_url"], headers)
    assert document["id"] == accepted["document_id"]
    assert document["original_filename"] == "fox.txt"
    assert document["csv_insights"] is None
    assert document["insights"] == {
        "char_count": 39,
        "char_count_no_whitespace": 30,
        "word_count": 9,
        "unique_word_count": 7,
        "sentence_count": 3,
        "paragraph_count": 2,
        "average_word_length": 3.0,
        "top_words": ["fox", "ran", "hid", "bird", "sang"],
        "estimated_reading_time_seconds": 2.7,
    }


@pytest.mark.integration
def test_csv_upload_goes_through_queue_and_worker_to_stored_insights(
    running_worker: None,
) -> None:
    headers = _register_and_log_in()
    accepted = _upload(headers, "people.csv", CSV)

    job = _wait_until_finished(accepted["status_url"], headers)

    assert job["state"] == "succeeded"
    document = _document(job["document_url"], headers)
    assert document["insights"] is None
    assert document["csv_insights"] == {
        "row_count": 2,
        "column_count": 2,
        "columns": [
            {
                "name": "name",
                "null_count": 0,
                "inferred_type": "string",
                "min": None,
                "max": None,
                "mean": None,
            },
            {
                "name": "age",
                "null_count": 0,
                "inferred_type": "integer",
                "min": 36.0,
                "max": 41.0,
                "mean": 38.5,
            },
        ],
    }
    listed = client.get("/documents", headers=headers).json()
    assert [d["id"] for d in listed["documents"]] == [accepted["document_id"]]


@pytest.mark.integration
def test_a_file_that_can_never_succeed_fails_once_with_its_reason(
    running_worker: None,
) -> None:
    headers = _register_and_log_in()
    accepted = _upload(headers, "latin1.txt", "café".encode("latin-1"))

    job = _wait_until_finished(accepted["status_url"], headers)

    assert job["state"] == "failed"
    assert job["attempts"] == 1
    assert job["last_error"] == "File is not valid UTF-8"
    document = _document(job["document_url"], headers)
    assert document["insights"] is None


@pytest.mark.integration
def test_a_passing_failure_is_requeued_through_redis_and_retried(
    running_worker: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The retry goes back through the real queue: the worker pushes the id
    to Redis again and picks it up on its next wait."""
    real_compute = job_processor.compute_insights
    calls = 0

    def fail_first_time(text: str) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("disk hiccup")
        return real_compute(text)

    monkeypatch.setattr(job_processor, "compute_insights", fail_first_time)
    headers = _register_and_log_in()
    accepted = _upload(headers, "fox.txt", TEXT.encode())

    job = _wait_until_finished(accepted["status_url"], headers)

    assert job["state"] == "succeeded"
    assert job["attempts"] == 2
    assert calls == 2
    document = _document(job["document_url"], headers)
    assert document["insights"]["word_count"] == 9
