from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppError
from app.core.request_context import REQUEST_ID_HEADER, get_request_id
from app.schemas.error import ErrorDetail, ErrorResponse


def _error_response(
    status_code: int, message: str, details: list[dict[str, Any]] | None = None
) -> JSONResponse:
    """Build the one error shape every failure returns.

    The request ID goes on the header as well as in the body. RequestIdMiddleware
    already sets it for responses that reach it, but an unhandled crash is caught
    above the middleware by Starlette's ServerErrorMiddleware and never does -
    and that is precisely the response whose ID a user needs in order to report
    the failure."""
    request_id = get_request_id()
    body = ErrorResponse(
        error=ErrorDetail(message=message, request_id=request_id, details=details)
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers={REQUEST_ID_HEADER: request_id} if request_id else None,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(422, "Request validation failed", details=exc.errors())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # The traceback belongs in the logs, tied to the request ID. The caller gets
    # a generic message - an exception string can carry a query, a file path or
    # a connection string.
    logger.exception("unhandled exception")
    return _error_response(500, "Internal server error")
