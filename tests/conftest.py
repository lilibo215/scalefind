"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.storage.local import LocalStore


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    allowlist = tmp_path / "subreddits.yaml"
    allowlist.write_text(
        "allowed_subreddits:\n  - example_subreddit_1\n  - example_subreddit_2\n",
        encoding="utf-8",
    )
    return Settings(
        REDDIT_CLIENT_ID="test_client_id",
        REDDIT_CLIENT_SECRET="test_client_secret",
        REDDIT_USER_AGENT="scalefind/0.1 test",
        REDDIT_REDIRECT_URI="http://localhost:8000/reddit/auth/callback",
        REDDIT_REQUEST_TIMEOUT_SECONDS=5,
        REDDIT_MAX_RETRIES=2,
        REDDIT_RATE_LIMIT_REQUESTS_PER_MINUTE=60,
        DATA_RETENTION_HOURS=24,
        STORAGE_PATH=tmp_path / "research.db",
        SUBREDDIT_ALLOWLIST_PATH=allowlist,
    )


@pytest.fixture
def store(settings: Settings) -> LocalStore:
    return LocalStore(settings.storage_path)


@pytest.fixture
def token_payload() -> dict:
    return {
        "access_token": "secret-access-token-value",
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": "*",
    }
