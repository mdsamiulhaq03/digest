from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    request_id: str | None = None
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
