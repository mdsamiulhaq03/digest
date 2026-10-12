import uuid

from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.cache import CACHE_VERSION, JsonCache, document_key
from app.core.circuit import CircuitBreaker
from tests.factories import FakeRedis


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
        cache = JsonCache(FakeRedis(error=error), 60)
        assert cache.get("k") is None
        cache.set("k", {"a": 1})  # must not raise
        cache.delete("k")  # must not raise


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
