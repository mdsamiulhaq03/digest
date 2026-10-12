"""A read-through cache in Redis that can never take a request down with it.

Every Redis failure is logged and treated as a miss, so an outage costs speed,
not availability: callers fall back to Postgres as if the cache weren't there.
"""

import json
import uuid
from functools import lru_cache
from typing import Any

import redis
from loguru import logger
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from app.core.circuit import CircuitBreaker
from app.core.config import get_settings

# Bump when the cached response shape changes: every old entry then simply
# misses after a deploy, instead of being served in the wrong shape.
CACHE_VERSION = "v1"

# A cache is only worth having if it is faster than the database it fronts. A
# slow Redis must give up quickly and let Postgres answer, not stall the read.
CACHE_SOCKET_TIMEOUT_SECONDS = 0.2


def document_key(owner_id: uuid.UUID, document_id: uuid.UUID) -> str:
    # The owner is part of the key, so a lookup by anyone else can only miss -
    # ownership is enforced by the key itself, as Phase 4 put it in the query.
    return f"doc:{CACHE_VERSION}:{owner_id}:{document_id}"


class JsonCache:
    def __init__(
        self,
        client: redis.Redis,
        ttl_seconds: int,
        breaker: CircuitBreaker | None = None,
    ) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._breaker = breaker or CircuitBreaker()

    def get(self, key: str) -> dict[str, Any] | None:
        if not self._breaker.allows_call():
            return None
        try:
            raw = self._client.get(key)
        except RedisError:
            self._breaker.record_failure()
            logger.warning("cache read failed, using database", cache_key=key)
            return None
        self._breaker.record_success()
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except ValueError:
            # Unreadable entry: treat as a miss; the next set() overwrites it.
            logger.warning("cache entry unreadable, ignoring", cache_key=key)
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self._breaker.allows_call():
            return
        try:
            self._client.set(key, json.dumps(value), ex=self._ttl_seconds)
        except RedisError:
            self._breaker.record_failure()
            logger.warning("cache write failed", cache_key=key)

    def delete(self, key: str) -> None:
        # Deliberately ignores the breaker: skipping a read or a write only
        # costs speed, but skipping a delete could leave stale data behind.
        # Deletes only happen off the request path, so their latency is free.
        try:
            self._client.delete(key)
        except RedisError:
            # The TTL still bounds how long the stale entry can live.
            logger.warning("cache delete failed", cache_key=key)


@lru_cache
def get_cache_client() -> redis.Redis:
    return connect_cache(get_settings().redis_url)


def connect_cache(url: str) -> redis.Redis:
    return redis.Redis.from_url(
        url,
        socket_timeout=CACHE_SOCKET_TIMEOUT_SECONDS,
        socket_connect_timeout=CACHE_SOCKET_TIMEOUT_SECONDS,
        # redis-py retries with backoff by default, which turned a 0.2s
        # timeout into ~6.6s of waiting on an unreachable Redis (measured).
        # For a cache, one fast attempt then Postgres is the right trade.
        retry=Retry(NoBackoff(), retries=0),
    )


@lru_cache
def get_document_cache() -> JsonCache:
    # One instance per process, so its circuit breaker sees every request.
    return JsonCache(get_cache_client(), get_settings().document_cache_ttl_seconds)
