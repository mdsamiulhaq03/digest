from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
