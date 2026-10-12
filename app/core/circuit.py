"""A minimal circuit breaker for optional dependencies (the cache, the queue).

When Redis is down, a call to it doesn't always fail fast: with its container
stopped, even resolving the hostname takes ~3.5s, and no socket timeout covers
that (measured). Paying that on every request would make an outage of an
*optional* dependency slow down everything. After one failure, the breaker
skips the dependency for a cooldown, so each process pays the cost at most
once per cooldown and notices recovery within one.
"""

import time
from collections.abc import Callable

# Long enough that an outage costs one slow call per process every few
# seconds rather than one per request; short enough that recovery is noticed
# almost immediately.
DEFAULT_COOLDOWN_SECONDS = 5.0


class CircuitBreaker:
    def __init__(
        self,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._open_until = 0.0

    def allows_call(self) -> bool:
        return self._clock() >= self._open_until

    def record_failure(self) -> None:
        self._open_until = self._clock() + self._cooldown_seconds

    def record_success(self) -> None:
        self._open_until = 0.0
