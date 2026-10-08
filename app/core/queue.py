"""The job queue: a Redis list of job ids. Postgres holds the jobs themselves,
so anything lost from here can be rebuilt from the jobs table."""

import uuid
from functools import lru_cache

import redis

from app.core.config import get_settings

JOB_QUEUE_KEY = "digest:jobs"


class JobQueue:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def enqueue(self, job_id: uuid.UUID) -> None:
        self._client.lpush(JOB_QUEUE_KEY, str(job_id))


@lru_cache
def get_redis() -> redis.Redis:
    # One client (and connection pool) per process. A short timeout means a
    # Redis outage fails fast instead of hanging the request that noticed it.
    return redis.Redis.from_url(get_settings().redis_url, socket_timeout=2)
