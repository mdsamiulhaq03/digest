import uuid
from collections.abc import Iterator

import pytest
from loguru import logger
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.cache import CACHE_VERSION, JsonCache, document_key
from app.core.circuit import CircuitBreaker
from tests.factories import FakeRedis


@pytest.fixture
def log_messages() -> Iterator[list[str]]:
    """The messages of warnings logged during the test."""
    messages: list[str] = []
    sink_id = logger.add(
        lambda message: messages.append(message.record["message"]), level="WARNING"
    )
    yield messages
    logger.remove(sink_id)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_key_contains_version_owner_and_document() -> None:
    owner, document = uuid.uuid4(), uuid.uuid4()
    assert document_key(owner, document) == f"doc:{CACHE_VERSION}:{owner}:{document}"


def test_same_document_different_owner_is_a_different_key() -> None:
    document = uuid.uuid4()
    assert document_key(uuid.uuid4(), document) != document_key(uuid.uuid4(), document)


def test_round_trip_and_ttl() -> None:
    client = FakeRedis()
    cache = JsonCache(client, ttl_seconds=3600)
    cache.set("k", {"title": "x", "n": 1})
    assert cache.get("k") == {"title": "x", "n": 1}
    assert client.ttls["k"] == 3600


def test_missing_key_is_none() -> None:
    assert JsonCache(FakeRedis(), 60).get("absent") is None


def test_delete_removes_the_entry() -> None:
    cache = JsonCache(FakeRedis(), 60)
    cache.set("k", {"a": 1})
    cache.delete("k")
    assert cache.get("k") is None


def test_redis_down_is_a_miss_not_an_error() -> None:
    for error in (RedisConnectionError("down"), RedisTimeoutError("slow")):
        assert JsonCache(FakeRedis(error=error), 60).get("k") is None


def test_a_failed_write_is_logged_and_opens_the_breaker(
    log_messages: list[str],
) -> None:
    client = FakeRedis()
    cache = JsonCache(client, 60, CircuitBreaker(cooldown_seconds=5, clock=FakeClock()))
    client.error = RedisConnectionError("down")

    cache.set("k", {"a": 1})

    assert "cache write failed" in log_messages
    client.error = None
    client.store = {"k": '{"a": 1}'}
    assert cache.get("k") is None  # breaker open: Redis not even asked


def test_a_failed_delete_is_logged_not_raised(log_messages: list[str]) -> None:
    JsonCache(FakeRedis(error=RedisConnectionError("down")), 60).delete("k")
    assert "cache delete failed" in log_messages


def test_after_a_failure_redis_is_skipped_until_the_cooldown_ends() -> None:
    clock = FakeClock()
    client = FakeRedis(error=RedisConnectionError("down"))
    cache = JsonCache(client, 60, CircuitBreaker(cooldown_seconds=5, clock=clock))

    assert cache.get("k") is None  # fails, opens the breaker
    client.error = None
    client.store = {"k": '{"a": 1}'}
    assert cache.get("k") is None  # still cooling down: Redis not even asked

    clock.now += 5
    assert cache.get("k") == {"a": 1}  # cooldown over, Redis back in use


def test_delete_is_attempted_even_while_the_breaker_is_open() -> None:
    clock = FakeClock()
    client = FakeRedis(error=RedisConnectionError("down"))
    cache = JsonCache(client, 60, CircuitBreaker(cooldown_seconds=5, clock=clock))
    cache.get("k")  # opens the breaker
    client.error = None
    client.store = {"k": "{}"}

    cache.delete("k")
    assert "k" not in client.store


def test_unreadable_entry_is_a_miss() -> None:
    client = FakeRedis()
    client.store = {"k": "not json{"}
    assert JsonCache(client, 60).get("k") is None
