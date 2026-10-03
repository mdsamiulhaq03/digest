import inspect
import logging
import sys

from loguru import logger

from app.core.config import get_settings
from app.core.request_context import get_request_id


def _inject_request_id(record: dict) -> None:
    record["extra"]["request_id"] = get_request_id()


class InterceptHandler(logging.Handler):
    """Funnel stdlib log records (uvicorn, SQLAlchemy) into loguru.

    Those libraries log through the standard library, not loguru, so without
    this a container's output is half JSON and half plain text - and the plain
    half carries no request ID, which defeats the point of having one."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Walk past logging's own frames so the line reports the module that
        # actually logged, not this handler or logging's internals.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    logger.remove()
    logger.configure(patcher=_inject_request_id)
    logger.add(sys.stdout, level=get_settings().log_level, serialize=True)

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for name in ("uvicorn", "uvicorn.error", "sqlalchemy.engine"):
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers = []
        stdlib_logger.propagate = True

    # RequestIdMiddleware already emits one access line per request, with the
    # request ID and duration attached. Uvicorn's own is a second, poorer line
    # for the same request, so it is silenced rather than intercepted.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = False
