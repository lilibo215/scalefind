"""Read-only post retrieval."""

from __future__ import annotations

import logging
from typing import Any

from app.reddit.client import RedditAPIError, RedditClient
from app.reddit.models import ResearchPost, normalize_post

logger = logging.getLogger(__name__)


def _normalize_post_id(post_id: str) -> str:
    cleaned = (post_id or "").strip()
    if cleaned.startswith("t3_"):
        cleaned = cleaned[3:]
    if not cleaned:
        raise ValueError("post id is required")
    if not cleaned.replace("_", "").isalnum():
        raise ValueError("post id contains invalid characters")
    return cleaned


async def get_post(client: RedditClient, post_id: str) -> ResearchPost:
    """Retrieve a specific public post when explicitly requested."""
    pid = _normalize_post_id(post_id)
    logger.info("reddit_post_lookup id=%s", pid)

    # /api/info is read-only and fetches by fullname
    payload = await client.get(
        "/api/info",
        params={"id": f"t3_{pid}", "raw_json": 1},
    )
    if not isinstance(payload, dict):
        raise RedditAPIError("Unexpected post response", category="parse_error")

    children = (
        payload.get("data", {}).get("children", [])
        if isinstance(payload.get("data"), dict)
        else []
    )
    if not children:
        raise RedditAPIError("Post not found", status_code=404, category="not_found")

    first = children[0]
    data: dict[str, Any] = first.get("data") if isinstance(first, dict) else {}
    if not data:
        raise RedditAPIError("Post not found", status_code=404, category="not_found")
    return normalize_post(data)
