from functools import lru_cache
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    log_level: str = "INFO"
    # No default: a missing secret should stop the app at startup, not fall
    # back to something guessable that would let anyone mint valid tokens.
    jwt_secret: str = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=60, gt=0)
    redis_url: str
    upload_dir: str = "/data/uploads"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    job_max_attempts: int = Field(default=3, gt=0)
    job_stuck_after_seconds: int = Field(default=300, gt=0)
    # Matches the token lifetime: a change made outside the app is visible for
    # at most as long as a revoked user's token keeps working anyway.
    document_cache_ttl_seconds: int = Field(default=3600, gt=0)
    # One-click logins to a demo user and a demo admin, for trying the app.
    # Off unless set: anywhere real, it would be a way in without a password.
    demo_accounts: bool = False
    # Browser origins allowed to call the API directly: exact origins,
    # comma-separated. Empty by default - the frontend's browser only ever
    # talks to Next.js, which calls the API server-side.
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _exact_origins_only(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            _check_origin(origin)
        return origins


def _check_origin(origin: str) -> None:
    if "*" in origin:
        # A wildcard lets any website's scripts read API responses in their
        # visitors' browsers. Refused outright rather than warned about.
        raise ValueError("CORS_ORIGINS must list exact origins, not '*'")
    parts = urlsplit(origin)
    if (
        parts.scheme not in ("http", "https")
        or not parts.netloc
        or parts.path
        or parts.query
        or parts.fragment
    ):
        # Browsers send the Origin header as scheme://host[:port] exactly, so
        # anything else - a trailing slash, a path - would silently never match.
        raise ValueError(
            f"CORS origin {origin!r} must look like https://app.example.com "
            "(scheme and host, optional port, no path or trailing slash)"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
