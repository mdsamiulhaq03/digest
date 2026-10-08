"""The job queue: a Redis list of job ids. Postgres holds the jobs themselves,
so anything lost from here can be rebuilt from the jobs table."""

import uuid
from functools import lru_cache

import redis

from app.core.config import get_settings

JOB_QUEUE_KEY = "digest:jobs"
# The API only ever pushes, so a Redis outage should fail it fast.
API_SOCKET_TIMEOUT_SECONDS = 2


class JobQueue:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def enqueue(self, job_id: uuid.UUID) -> None:
        self._client.lpush(JOB_QUEUE_KEY, str(job_id))

    def dequeue(self, wait_seconds: int) -> str | None:
        """Block up to wait_seconds for the next id. Returned raw: whatever is
        in Redis is untrusted until the caller has parsed it."""
        item = self._client.brpop([JOB_QUEUE_KEY], timeout=wait_seconds)
        return None if item is None else item[1].decode()


def connect(socket_timeout: float) -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, socket_timeout=socket_timeout)


@lru_cache
def get_redis() -> redis.Redis:
    # One client (and connection pool) per process.
    return connect(API_SOCKET_TIMEOUT_SECONDS)
