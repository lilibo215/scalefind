"""User-initiated Reddit search (read-only)."""

from __future__ import annotations

import logging
from typing import Any

from app.reddit.client import RedditClient
from app.reddit.models import ResearchPost, normalize_post

logger = logging.getLogger(__name__)


async def search(
    client: RedditClient,
    query: str,
    *,
    subreddit: str | None = None,
    limit: int = 10,
) -> list[ResearchPost]:
    """Search public Reddit content. Returns minimized research records."""
    q = (query or "").strip()
    if not q:
        raise ValueError("query is required")
    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25")

    params: dict[str, Any] = {
        "q": q,
        "limit": limit,
        "sort": "relevance",
        "type": "link",
        "raw_json": 1,
    }

    if subreddit:
        name = subreddit.strip().lstrip("r/")
        path = f"/r/{name}/search"
        params["restrict_sr"] = "true"
    else:
        path = "/search"

    logger.info(
        "reddit_search query_len=%s subreddit=%s limit=%s",
        len(q),
        subreddit or "all",
        limit,
    )
    payload = await client.get(path, params=params)
    if not isinstance(payload, dict):
        return []

    children = (
        payload.get("data", {}).get("children", [])
        if isinstance(payload.get("data"), dict)
        else []
    )
    results: list[ResearchPost] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        data = child.get("data")
        if isinstance(data, dict):
            results.append(normalize_post(data))
    return results
