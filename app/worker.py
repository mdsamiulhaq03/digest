"""The background worker: `python -m app.worker`.

Waits on the Redis list for job ids and hands each to the job processor.
Runs the same image as the API with a different command."""

import time
import uuid

from loguru import logger
from redis.exceptions import RedisError

from app.core.logging import configure_logging
from app.core.queue import JobQueue, connect
from app.core.request_context import set_request_id
from app.services.job_processor import process_job

# How long one wait on Redis lasts. Short enough that the loop regularly gets
# a chance to notice it should stop; the socket timeout must outlast it.
POLL_SECONDS = 5
SOCKET_TIMEOUT_SECONDS = POLL_SECONDS + 5
REDIS_RETRY_SECONDS = 1


def run() -> None:
    configure_logging()
    queue = JobQueue(connect(SOCKET_TIMEOUT_SECONDS))
    logger.info("worker started")
    while True:
        _handle_next(queue)


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
