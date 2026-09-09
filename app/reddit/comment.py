"""Read-only comment retrieval with depth/count limits."""

from __future__ import annotations

import logging
from typing import Any

from app.reddit.client import RedditAPIError, RedditClient
from app.reddit.models import ResearchComment, normalize_comment

logger = logging.getLogger(__name__)


def _normalize_post_id(post_id: str) -> str:
    cleaned = (post_id or "").strip()
    if cleaned.startswith("t3_"):
        cleaned = cleaned[3:]
    if not cleaned:
        raise ValueError("post id is required")
    return cleaned


def _walk_comments(
    node: Any,
    *,
    post_id: str,
    depth: int,
    max_depth: int,
    max_count: int,
    out: list[ResearchComment],
) -> None:
    if len(out) >= max_count or depth > max_depth:
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    data = node.get("data")
    if kind == "t1" and isinstance(data, dict):
        out.append(normalize_comment(data, post_id=post_id, depth=depth))
        replies = data.get("replies")
        if isinstance(replies, dict):
            children = replies.get("data", {}).get("children", [])
            if isinstance(children, list):
                for child in children:
                    _walk_comments(
                        child,
                        post_id=post_id,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_count=max_count,
                        out=out,
                    )
    elif kind == "Listing" and isinstance(data, dict):
        children = data.get("children", [])
        if isinstance(children, list):
            for child in children:
                _walk_comments(
                    child,
                    post_id=post_id,
                    depth=depth,
                    max_depth=max_depth,
                    max_count=max_count,
                    out=out,
                )


async def get_comments(
    client: RedditClient,
    post_id: str,
    *,
    subreddit: str | None = None,
    max_depth: int = 2,
    max_count: int = 50,
) -> list[ResearchComment]:
    """Retrieve comments for a specific post with configurable limits."""
    if max_depth < 0 or max_depth > 5:
        raise ValueError("max_depth must be between 0 and 5")
    if max_count < 1 or max_count > 100:
        raise ValueError("max_count must be between 1 and 100")

    pid = _normalize_post_id(post_id)
    logger.info(
        "reddit_comments_lookup id=%s max_depth=%s max_count=%s",
        pid,
        max_depth,
        max_count,
    )

    # Prefer /comments/{article} which returns [post_listing, comment_listing]
    # Subreddit path is optional; article endpoint works with just the id.
    if subreddit:
        name = subreddit.strip().lstrip("r/")
        path = f"/r/{name}/comments/{pid}"
    else:
        path = f"/comments/{pid}"

    payload = await client.get(
        path,
        params={"limit": max_count, "depth": max_depth, "raw_json": 1, "sort": "confidence"},
    )
    if not isinstance(payload, list) or len(payload) < 2:
        raise RedditAPIError("Unexpected comments response", category="parse_error")

    comment_listing = payload[1]
    out: list[ResearchComment] = []
    _walk_comments(
        comment_listing,
        post_id=pid,
        depth=0,
        max_depth=max_depth,
        max_count=max_count,
        out=out,
    )
    return out
