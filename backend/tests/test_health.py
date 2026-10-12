"""Liveness and readiness. Liveness must never depend on anything outside the
process; readiness fails only on Postgres, and reports Redis without failing."""

import time
from collections.abc import Iterator

import pytest
import redis
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from app.core.db import get_db
from app.main import app
from app.routers.dependencies import get_health_redis, get_health_repository
from app.services import health_service
from tests.factories import FakeRedis

client = TestClient(app)


class StubHealthRepository:
    def __init__(self, reachable: bool) -> None:
        self.reachable = reachable

    def ping(self) -> None:
        if not self.reachable:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))


@pytest.fixture
def dependencies() -> Iterator[None]:
    yield
    for dependency in (get_db, get_health_repository, get_health_redis):
        app.dependency_overrides.pop(dependency, None)


def _set(postgres_up: bool, redis_up: bool) -> None:
    error = None if redis_up else RedisConnectionError("down")
    app.dependency_overrides[get_health_repository] = lambda: StubHealthRepository(
        postgres_up
    )
    app.dependency_overrides[get_health_redis] = lambda: FakeRedis(error=error)


@pytest.mark.parametrize("path", ["/health/live", "/health"])
def test_liveness_never_touches_a_dependency(path: str, dependencies: None) -> None:
    def no_database() -> None:
        raise AssertionError("liveness opened a database session")

    app.dependency_overrides[get_db] = no_database
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_everything_is_up(dependencies: None) -> None:
    _set(postgres_up=True, redis_up=True)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "ok"}


def test_not_ready_without_postgres(dependencies: None) -> None:
    _set(postgres_up=False, redis_up=True)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "postgres": "unavailable",
        "redis": "ok",
    }


def test_still_ready_without_redis_but_says_degraded(dependencies: None) -> None:
    _set(postgres_up=True, redis_up=False)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "degraded"}


def test_liveness_stays_up_while_readiness_is_down(dependencies: None) -> None:
    """The whole point of two endpoints: a dead database makes the instance
    unready, but must not make it look broken enough to restart."""
    _set(postgres_up=False, redis_up=False)
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/live").status_code == 200


@pytest.mark.integration
def test_ready_against_the_real_postgres_and_redis(real_redis: redis.Redis) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "ok"}


class HangingRedis(FakeRedis):
    """A Redis whose hostname lookup hangs, as when its container is stopped."""

    def ping(self) -> bool:
        time.sleep(1)
        return True


def test_a_hanging_redis_is_reported_degraded_within_the_deadline(
    dependencies: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_service, "REDIS_PROBE_TIMEOUT_SECONDS", 0.1)
    app.dependency_overrides[get_health_repository] = lambda: StubHealthRepository(True)
    app.dependency_overrides[get_health_redis] = lambda: HangingRedis()

    started = time.monotonic()
    response = client.get("/health/ready")

    assert time.monotonic() - started < 0.8  # never waited out the 1s hang
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "postgres": "ok", "redis": "degraded"}
