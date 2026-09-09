"""Search, subreddit, post, and comment retrieval tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import Settings
from app.reddit.client import RedditClient
from app.reddit.comment import get_comments
from app.reddit.post import get_post
from app.reddit.search import search
from app.reddit.subreddit import get_subreddit, is_allowed, load_allowlist


def _auth_route(token_payload: dict):
    return respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(200, json=token_payload)
    )


@pytest.mark.asyncio
@respx.mock
async def test_search(settings: Settings, token_payload: dict):
    _auth_route(token_payload)
    respx.get("https://oauth.reddit.com/search").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "children": [
                        {
                            "kind": "t3",
                            "data": {
                                "id": "abc123",
                                "title": "Example post",
                                "selftext": "Short body text for research",
                                "subreddit": "example_subreddit_1",
                                "created_utc": 1700000000,
                                "permalink": "/r/example_subreddit_1/comments/abc123/example/",
                                "score": 10,
                                "num_comments": 2,
                            },
                        }
                    ]
                }
            },
            headers={"x-ratelimit-remaining": "59", "x-ratelimit-used": "1", "x-ratelimit-reset": "60"},
        )
    )
    async with RedditClient(settings) as client:
        results = await search(client, "example query", limit=5)
    assert len(results) == 1
    assert results[0].reddit_id == "abc123"
    assert results[0].title == "Example post"
    assert results[0].subreddit == "example_subreddit_1"
    assert results[0].permalink.startswith("https://www.reddit.com/")


@pytest.mark.asyncio
@respx.mock
async def test_subreddit_lookup(settings: Settings, token_payload: dict):
    _auth_route(token_payload)
    respx.get("https://oauth.reddit.com/r/example_subreddit_1/about").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "display_name": "example_subreddit_1",
                    "title": "Example",
                    "public_description": "Public desc",
                    "subscribers": 123,
                }
            },
        )
    )
    async with RedditClient(settings) as client:
        info = await get_subreddit(client, "example_subreddit_1")
    assert info.exists is True
    assert info.accessible is True
    assert info.subscribers == 123


def test_allowlist_loading(settings: Settings):
    allowlist = load_allowlist(settings.subreddit_allowlist_path)
    assert "example_subreddit_1" in allowlist
    assert is_allowed("example_subreddit_1", allowlist)
    assert not is_allowed("not_listed", allowlist)


@pytest.mark.asyncio
@respx.mock
async def test_post_retrieval(settings: Settings, token_payload: dict):
    _auth_route(token_payload)
    respx.get("https://oauth.reddit.com/api/info").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "children": [
                        {
                            "kind": "t3",
                            "data": {
                                "id": "post99",
                                "title": "A post",
                                "selftext": "Body",
                                "subreddit": "example_subreddit_1",
                                "created_utc": 1700000000,
                                "permalink": "/r/example_subreddit_1/comments/post99/a_post/",
                                "score": 5,
                                "num_comments": 1,
                            },
                        }
                    ]
                }
            },
        )
    )
    async with RedditClient(settings) as client:
        post = await get_post(client, "post99")
    assert post.reddit_id == "post99"
    assert post.title == "A post"


@pytest.mark.asyncio
@respx.mock
async def test_comment_retrieval(settings: Settings, token_payload: dict):
    _auth_route(token_payload)
    respx.get("https://oauth.reddit.com/comments/post99").mock(
        return_value=Response(
            200,
            json=[
                {"kind": "Listing", "data": {"children": []}},
                {
                    "kind": "Listing",
                    "data": {
                        "children": [
                            {
                                "kind": "t1",
                                "data": {
                                    "id": "cmt1",
                                    "body": "Top comment",
                                    "link_id": "t3_post99",
                                    "subreddit": "example_subreddit_1",
                                    "created_utc": 1700000100,
                                    "permalink": "/r/example_subreddit_1/comments/post99/a_post/cmt1/",
                                    "score": 3,
                                    "replies": {
                                        "kind": "Listing",
                                        "data": {
                                            "children": [
                                                {
                                                    "kind": "t1",
                                                    "data": {
                                                        "id": "cmt2",
                                                        "body": "Reply",
                                                        "link_id": "t3_post99",
                                                        "created_utc": 1700000200,
                                                        "score": 1,
                                                        "replies": "",
                                                    },
                                                }
                                            ]
                                        },
                                    },
                                },
                            }
                        ]
                    },
                },
            ],
        )
    )
    async with RedditClient(settings) as client:
        comments = await get_comments(client, "post99", max_depth=2, max_count=10)
    assert len(comments) == 2
    assert comments[0].reddit_id == "cmt1"
    assert comments[1].depth == 1
