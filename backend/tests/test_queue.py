import uuid

from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.circuit import CircuitBreaker
from app.core.queue import JobQueue


class FakeListRedis:
    def __init__(self) -> None:
        self.down = False
        self.pushes = 0

    def lpush(self, key: str, value: str) -> None:
        self.pushes += 1
        if self.down:
            raise RedisConnectionError("down")


def test_after_a_failed_push_redis_is_not_retried_until_the_cooldown_ends() -> None:
    now = [0.0]
    client = FakeListRedis()
    queue = JobQueue(client, CircuitBreaker(cooldown_seconds=5, clock=lambda: now[0]))

    client.down = True
    assert queue.try_enqueue(uuid.uuid4()) is False  # one slow failure...
    assert queue.try_enqueue(uuid.uuid4()) is False  # ...then skipped
    assert client.pushes == 1

    client.down = False
    now[0] += 5
    assert queue.try_enqueue(uuid.uuid4()) is True
    assert client.pushes == 2
