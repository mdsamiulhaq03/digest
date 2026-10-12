"""The job queue: a Redis list of job ids. Postgres holds the jobs themselves,
so anything lost from here can be rebuilt from the jobs table."""

import uuid
from functools import lru_cache

import redis
from loguru import logger
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from app.core.circuit import CircuitBreaker
from app.core.config import get_settings

JOB_QUEUE_KEY = "digest:jobs"
# The API only ever pushes, so a Redis outage should fail it fast.
API_SOCKET_TIMEOUT_SECONDS = 2


class JobQueue:
    def __init__(
        self, client: redis.Redis, breaker: CircuitBreaker | None = None
    ) -> None:
        self._client = client
        self._breaker = breaker or CircuitBreaker()

    def enqueue(self, job_id: uuid.UUID) -> None:
        self._client.lpush(JOB_QUEUE_KEY, str(job_id))

    def try_enqueue(self, job_id: uuid.UUID) -> bool:
        """Enqueue, or leave it to the sweeper if Redis is unavailable.

        Only for jobs already committed as queued in Postgres: there, a lost
        push just delays the job until the next sweep, so failing the caller
        would gain nothing. After a failure the breaker skips Redis for a few
        seconds, so an outage doesn't add seconds to every upload."""
        if not self._breaker.allows_call():
            logger.warning(
                "redis recently failed, sweeper will enqueue", job_id=str(job_id)
            )
            return False
        try:
            self.enqueue(job_id)
        except RedisError:
            self._breaker.record_failure()
            logger.warning("enqueue failed, sweeper will retry", job_id=str(job_id))
            return False
        self._breaker.record_success()
        return True

    def dequeue(self, wait_seconds: int) -> str | None:
        """Block up to wait_seconds for the next id. Returned raw: whatever is
        in Redis is untrusted until the caller has parsed it."""
        item = self._client.brpop([JOB_QUEUE_KEY], timeout=wait_seconds)
        return None if item is None else item[1].decode()


def connect(socket_timeout: float) -> redis.Redis:
    return redis.Redis.from_url(
        get_settings().redis_url,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_timeout,
        # redis-py retries with backoff by default, multiplying the timeout.
        # Both callers already recover on their own - the API leaves the job
        # to the sweeper, the worker waits and loops - so fail fast instead.
        retry=Retry(NoBackoff(), retries=0),
    )


@lru_cache
def get_redis() -> redis.Redis:
    # One client (and connection pool) per process.
    return connect(API_SOCKET_TIMEOUT_SECONDS)
