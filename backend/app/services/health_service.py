from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

import redis
from loguru import logger
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.health_repository import HealthRepository
from app.schemas.health import ReadinessResponse

# With the Redis container stopped, resolving its hostname takes ~3.5s and no
# socket timeout covers that (measured in Phase 6). Readiness must answer well
# inside its caller's timeout (Compose allows 3s), or an optional dependency
# would make the API look unready. So the Redis probe gets a hard deadline.
REDIS_PROBE_TIMEOUT_SECONDS = 0.5

# A probe that overruns keeps its thread until the lookup gives up; a small
# pool bounds how many can pile up.
_redis_probes = ThreadPoolExecutor(max_workers=2, thread_name_prefix="redis-probe")


def check_readiness(
    repo: HealthRepository, redis_client: redis.Redis
) -> ReadinessResponse:
    redis_probe = _redis_probes.submit(_redis_reachable, redis_client)
    postgres_ok = _postgres_reachable(repo)
    redis_ok = _within_deadline(redis_probe)
    return ReadinessResponse(
        status="ready" if postgres_ok else "not_ready",
        postgres="ok" if postgres_ok else "unavailable",
        redis="ok" if redis_ok else "degraded",
    )


def _postgres_reachable(repo: HealthRepository) -> bool:
    # Not given a deadline like Redis: it uses the request's session, which
    # must not be touched from another thread. A slow answer here is still a
    # failure, so the outcome is right either way.
    try:
        repo.ping()
    except SQLAlchemyError:
        logger.warning("readiness: postgres unreachable")
        return False
    return True


def _redis_reachable(redis_client: redis.Redis) -> bool:
    try:
        redis_client.ping()
    except RedisError:
        logger.warning("readiness: redis unreachable, running degraded")
        return False
    return True


def _within_deadline(redis_probe: Future[bool]) -> bool:
    try:
        return redis_probe.result(timeout=REDIS_PROBE_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        logger.warning("readiness: redis probe timed out, running degraded")
        return False
