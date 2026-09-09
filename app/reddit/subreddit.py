"""Read-only subreddit lookup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from app.reddit.client import RedditAPIError, RedditClient
from app.reddit.models import SubredditInfo

logger = logging.getLogger(__name__)


def load_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    items = data.get("allowed_subreddits") or []
    return {str(x).strip().lstrip("r/").lower() for x in items if str(x).strip()}


def is_allowed(name: str, allowlist: set[str]) -> bool:
    """If allowlist is empty, treat as unrestricted for local development.

    For Reddit app review, populate config/subreddits.yaml explicitly.
    """
    normalized = name.strip().lstrip("r/").lower()
    if not allowlist:
        return True
    return normalized in allowlist


async def get_subreddit(client: RedditClient, name: str) -> SubredditInfo:
    cleaned = (name or "").strip().lstrip("r/")
    if not cleaned:
        raise ValueError("subreddit name is required")
    if not cleaned.replace("_", "").isalnum():
        raise ValueError("subreddit name contains invalid characters")

    logger.info("reddit_subreddit_lookup name=%s", cleaned)
    try:
        payload = await client.get(f"/r/{cleaned}/about", params={"raw_json": 1})
    except RedditAPIError as exc:
        if exc.status_code in {403, 404}:
            return SubredditInfo(
                name=cleaned,
                exists=exc.status_code != 404,
                accessible=False,
            )
        raise

    if not isinstance(payload, dict):
        return SubredditInfo(name=cleaned, exists=False, accessible=False)

    data: dict[str, Any] = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if not data:
        return SubredditInfo(name=cleaned, exists=False, accessible=False)

    return SubredditInfo(
        name=cleaned,
        display_name=data.get("display_name"),
        title=data.get("title"),
        public_description=data.get("public_description"),
        subscribers=data.get("subscribers"),
        exists=True,
        accessible=True,
    )
