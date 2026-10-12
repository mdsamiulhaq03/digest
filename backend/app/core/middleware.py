import re
import time
import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import REQUEST_ID_HEADER, set_request_id

# A client-supplied id is written into every log line for the request, so it
# is only trusted if it is short and plain. Anything else - oversized, or
# carrying newlines or quotes that could forge log entries - is replaced.
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")


def _resolve_request_id(client_value: str | None) -> str:
    if client_value and _SAFE_REQUEST_ID.fullmatch(client_value):
        return client_value
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = _resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        set_request_id(request_id)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request handled",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
            )
