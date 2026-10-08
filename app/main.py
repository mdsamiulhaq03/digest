from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.error_handlers import (
    app_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.routers import admin, auth, documents, health

configure_logging()

app = FastAPI(title="Digest")

app.add_middleware(RequestIdMiddleware)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(admin.router)
