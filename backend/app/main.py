from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.cors import add_cors
from app.core.error_handlers import (
    app_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.routers import admin, auth, demo, documents, health, jobs

configure_logging()

app = FastAPI(title="Digest")

# Added first, so RequestIdMiddleware wraps it: preflight requests get a
# request id and an access-log line like any other.
add_cors(app, get_settings().cors_origins)
app.add_middleware(RequestIdMiddleware)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(demo.router)
app.include_router(documents.router)
app.include_router(jobs.router)
app.include_router(admin.router)
