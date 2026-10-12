"""The worker loop with no Redis or Postgres: a scripted queue and stubs."""

import threading
import uuid

import pytest

from app import worker


class ScriptedQueue:
    """Hands out a fixed sequence of raw ids, then signals stop."""

    def __init__(self, raw_ids: list[str | None], stop: threading.Event) -> None:
        self._raw_ids = list(raw_ids)
        self._stop = stop

    def dequeue(self, wait_seconds: int) -> str | None:
        if not self._raw_ids:
            self._stop.set()
            return None
        return self._raw_ids.pop(0)


@pytest.fixture
def processed(monkeypatch: pytest.MonkeyPatch) -> list[uuid.UUID]:
    handled: list[uuid.UUID] = []
    monkeypatch.setattr(
        worker, "process_job", lambda job_id, queue: handled.append(job_id)
    )
    monkeypatch.setattr(worker, "sweep", lambda queue: None)
    return handled


def test_processes_each_valid_id_then_stops(processed: list[uuid.UUID]) -> None:
    first, second = uuid.uuid4(), uuid.uuid4()
    stop = threading.Event()
    worker.run_loop(ScriptedQueue([str(first), None, str(second)], stop), stop)
    assert processed == [first, second]


def test_malformed_ids_are_discarded_not_fatal(processed: list[uuid.UUID]) -> None:
    good = uuid.uuid4()
    stop = threading.Event()
    worker.run_loop(ScriptedQueue(["not-a-uuid", str(good)], stop), stop)
    assert processed == [good]


def test_stop_lets_the_current_job_finish(monkeypatch: pytest.MonkeyPatch) -> None:
    stop = threading.Event()
    finished: list[uuid.UUID] = []

    def slow_job(job_id: uuid.UUID, queue: object) -> None:
        stop.set()  # SIGTERM arrives mid-job...
        finished.append(job_id)  # ...and the job still completes

    monkeypatch.setattr(worker, "process_job", slow_job)
    monkeypatch.setattr(worker, "sweep", lambda queue: None)
    job_id = uuid.uuid4()
    worker.run_loop(ScriptedQueue([str(job_id), str(uuid.uuid4())], stop), stop)

    # The job in hand finished; the next one was never taken.
    assert finished == [job_id]


def test_sweeps_on_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    sweeps: list[object] = []
    monkeypatch.setattr(worker, "sweep", lambda queue: sweeps.append(queue))
    stop = threading.Event()
    queue = ScriptedQueue([], stop)
    worker.run_loop(queue, stop)
    assert sweeps == [queue]
