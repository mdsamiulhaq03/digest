"""The background worker: `python -m app.worker`.

Waits on the Redis list for job ids and hands each to the job processor, and
runs the sweeper on startup and then every SWEEP_INTERVAL_SECONDS. Runs the
same image as the API with a different command."""

import signal
import threading
import time
import uuid

from loguru import logger
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import configure_logging
from app.core.queue import JobQueue, connect
from app.core.request_context import set_request_id
from app.services.job_processor import process_job
from app.services.sweeper import sweep

# How long one wait on Redis lasts. It bounds how long a stop request can go
# unnoticed while idle; the socket timeout must outlast it.
POLL_SECONDS = 5
SOCKET_TIMEOUT_SECONDS = POLL_SECONDS + 5
REDIS_RETRY_SECONDS = 1
SWEEP_INTERVAL_SECONDS = 60


def run() -> None:
    configure_logging()
    stop = threading.Event()
    # SIGTERM is what `docker compose stop` sends. The handler only raises a
    # flag: a job in progress runs to completion, then the loop exits, so
    # nothing is dropped half-done.
    # Nothing but stop.set() runs inside the handler - logging there could
    # deadlock on the logger's lock if the signal lands mid-write.
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    run_loop(JobQueue(connect(SOCKET_TIMEOUT_SECONDS)), stop)


def run_loop(queue: JobQueue, stop: threading.Event) -> None:
    logger.info("worker started")
    next_sweep_at = 0.0  # sweep immediately: recover whatever a crash left
    while not stop.is_set():
        if time.monotonic() >= next_sweep_at:
            _sweep_safely(queue)
            next_sweep_at = time.monotonic() + SWEEP_INTERVAL_SECONDS
        _handle_next(queue)
    logger.info("worker stopped cleanly")


def _sweep_safely(queue: JobQueue) -> None:
    set_request_id("sweeper")
    try:
        sweep(queue)
    except SQLAlchemyError:
        # A sweep that can't reach Postgres is retried at the next interval.
        logger.exception("sweep failed")


def _handle_next(queue: JobQueue) -> None:
    try:
        raw_id = queue.dequeue(POLL_SECONDS)
    except RedisError:
        logger.warning("redis unavailable, retrying")
        time.sleep(REDIS_RETRY_SECONDS)
        return
    if raw_id is None:
        return

    try:
        job_id = uuid.UUID(raw_id)
    except ValueError:
        logger.warning("discarded malformed job id from queue")
        return

    # Reuse the request-id context so every log line for this job carries
    # its id, exactly as API log lines carry their request's id.
    set_request_id(f"job-{job_id}")
    process_job(job_id, queue)


if __name__ == "__main__":
    run()
