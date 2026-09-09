"""Normalized research record models (data-minimized)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_from_reddit(created_utc: float | int | None) -> datetime | None:
    if created_utc is None:
        return None
    return datetime.fromtimestamp(float(created_utc), tz=timezone.utc)


class ResearchPost(BaseModel):
    reddit_id: str
    title: str
    body: str | None = None
    subreddit: str
    created_at: datetime | None = None
    permalink: str
    score: int | None = None
    comment_count: int | None = None
    kind: str = "post"


class ResearchComment(BaseModel):
    reddit_id: str
    body: str | None = None
    post_id: str
    subreddit: str | None = None
    created_at: datetime | None = None
    permalink: str | None = None
    score: int | None = None
    depth: int = 0
    kind: str = "comment"


class SubredditInfo(BaseModel):
    name: str
    display_name: str | None = None
    title: str | None = None
    public_description: str | None = None
    subscribers: int | None = None
    exists: bool = True
    accessible: bool = True


def normalize_post(data: dict[str, Any]) -> ResearchPost:
    permalink = data.get("permalink") or ""
    if permalink and not permalink.startswith("http"):
        permalink = f"https://www.reddit.com{permalink}"
    body = data.get("selftext") or data.get("body")
    if isinstance(body, str) and len(body) > 500:
        body = body[:497] + "..."
    return ResearchPost(
        reddit_id=str(data.get("id") or data.get("name") or ""),
        title=str(data.get("title") or ""),
        body=body or None,
        subreddit=str(data.get("subreddit") or ""),
        created_at=utc_from_reddit(data.get("created_utc")),
        permalink=permalink,
        score=data.get("score"),
        comment_count=data.get("num_comments"),
    )


def normalize_comment(
    data: dict[str, Any],
    *,
    post_id: str,
    depth: int = 0,
) -> ResearchComment:
    permalink = data.get("permalink")
    if isinstance(permalink, str) and permalink and not permalink.startswith("http"):
        permalink = f"https://www.reddit.com{permalink}"
    body = data.get("body")
    if isinstance(body, str) and len(body) > 500:
        body = body[:497] + "..."
    link_id = data.get("link_id") or post_id
    if isinstance(link_id, str) and link_id.startswith("t3_"):
        link_id = link_id[3:]
    return ResearchComment(
        reddit_id=str(data.get("id") or ""),
        body=body,
        post_id=str(link_id),
        subreddit=data.get("subreddit"),
        created_at=utc_from_reddit(data.get("created_utc")),
        permalink=permalink,
        score=data.get("score"),
        depth=depth,
    )


class StoredRecord(BaseModel):
    reddit_id: str
    kind: str
    payload_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
