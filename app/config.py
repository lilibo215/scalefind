"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    reddit_client_id: str = Field(default="", alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(default="", alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(
        default="scalefind/0.1",
        alias="REDDIT_USER_AGENT",
    )
    reddit_redirect_uri: str = Field(
        default="http://localhost:8000/reddit/auth/callback",
        alias="REDDIT_REDIRECT_URI",
    )

    reddit_request_timeout_seconds: float = Field(
        default=15.0, alias="REDDIT_REQUEST_TIMEOUT_SECONDS"
    )
    reddit_max_retries: int = Field(default=3, alias="REDDIT_MAX_RETRIES")
    reddit_rate_limit_requests_per_minute: int = Field(
        default=60, alias="REDDIT_RATE_LIMIT_REQUESTS_PER_MINUTE"
    )

    data_retention_hours: int = Field(default=24, alias="DATA_RETENTION_HOURS")
    storage_path: Path = Field(default=Path("data/research.db"), alias="STORAGE_PATH")
    subreddit_allowlist_path: Path = Field(
        default=Path("config/subreddits.yaml"),
        alias="SUBREDDIT_ALLOWLIST_PATH",
    )

    @field_validator("reddit_max_retries")
    @classmethod
    def _validate_retries(cls, value: int) -> int:
        if value < 0 or value > 10:
            raise ValueError("REDDIT_MAX_RETRIES must be between 0 and 10")
        return value

    @field_validator("data_retention_hours")
    @classmethod
    def _validate_retention(cls, value: int) -> int:
        if value < 1:
            raise ValueError("DATA_RETENTION_HOURS must be >= 1")
        return value

    def credentials_present(self) -> bool:
        return bool(self.reddit_client_id.strip() and self.reddit_client_secret.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
