from collections.abc import Mapping
from typing import ClassVar


class AppError(Exception):
    status_code = 500
    headers: ClassVar[Mapping[str, str] | None] = None

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class DocumentNotFoundError(NotFoundError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document {document_id} not found")
        self.document_id = document_id


class JobNotFoundError(NotFoundError):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job {job_id} not found")
        self.job_id = job_id


class AuthenticationError(AppError):
    status_code = 401
    # RFC 9110: a 401 must tell the client which scheme to authenticate with.
    headers: ClassVar[Mapping[str, str]] = {"WWW-Authenticate": "Bearer"}


class InvalidTokenError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Invalid authentication token")


class TokenExpiredError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Authentication token has expired")


class InvalidCredentialsError(AuthenticationError):
    # One message for "no such email" and "wrong password", so login can't be
    # used to discover which emails have accounts.
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class PermissionDeniedError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Email is already registered")


class UnsupportedFileTypeError(AppError):
    status_code = 415

    def __init__(self, allowed_extensions: list[str]) -> None:
        super().__init__(f"Only {', '.join(allowed_extensions)} files are accepted")


class FileTooLargeError(AppError):
    status_code = 413

    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            f"File is larger than the {max_bytes // (1024 * 1024)} MB limit"
        )
