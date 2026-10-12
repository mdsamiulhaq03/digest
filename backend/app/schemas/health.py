from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    """The process is up and answering. Says nothing about dependencies."""

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    """Whether this instance can serve requests right now, and why not.

    Only Postgres decides `status`: without it no request can be served.
    Redis is reported but never makes the instance unready - the cache falls
    back to Postgres and the sweeper re-queues uploads, so a Redis outage
    costs speed, not service."""

    status: Literal["ready", "not_ready"]
    postgres: Literal["ok", "unavailable"]
    redis: Literal["ok", "degraded"]
