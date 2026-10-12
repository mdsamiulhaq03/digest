"""Liveness and readiness - two questions with different consumers.

Liveness: is this process broken in a way a restart would fix? It checks
nothing external. If it checked Postgres, a database blip would fail every
API container at once and the orchestrator would restart them all together -
turning someone else's outage into our own.

Readiness: can this instance serve requests right now? It checks Postgres, so
traffic (and anything waiting on the API, like the worker in Compose) holds
off until it can. A failure means "wait", never "restart".
"""

import redis
from fastapi import APIRouter, Depends, Response, status

from app.repositories.health_repository import HealthRepository
from app.routers.dependencies import get_health_redis, get_health_repository
from app.schemas.health import LivenessResponse, ReadinessResponse
from app.services import health_service

router = APIRouter(tags=["health"])


# /health is the original endpoint, kept as an alias so existing callers
# (scripts, docs, anything polling it) keep working.
@router.get("/health", response_model=LivenessResponse)
@router.get("/health/live", response_model=LivenessResponse)
def live() -> LivenessResponse:
    return LivenessResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
def ready(
    response: Response,
    repo: HealthRepository = Depends(get_health_repository),
    redis_client: redis.Redis = Depends(get_health_redis),
) -> ReadinessResponse:
    report = health_service.check_readiness(repo, redis_client)
    if report.status == "not_ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
