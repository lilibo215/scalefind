"""Rate limiting and retry behavior tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import Settings
from app.reddit.client import RedditAPIError, RedditClient
from app.reddit.rate_limit import RateLimiter


def test_backoff_exponential():
    limiter = RateLimiter(max_retries=3, base_backoff_seconds=1.0, max_backoff_seconds=30.0)
    assert limiter.backoff_seconds(0) == 1.0
    assert limiter.backoff_seconds(1) == 2.0
    assert limiter.backoff_seconds(2) == 4.0


def test_backoff_respects_retry_after_cap():
    limiter = RateLimiter(max_backoff_seconds=5.0)
    assert limiter.backoff_seconds(0, retry_after=100) == 5.0


def test_should_retry_limits():
    limiter = RateLimiter(max_retries=2)
    assert limiter.should_retry(0, 429) is True
    assert limiter.should_retry(1, 503) is True
    assert limiter.should_retry(2, 429) is False
    assert limiter.should_retry(0, 400) is False


def test_update_from_headers():
    limiter = RateLimiter()
    limiter.update_from_headers(
        {
            "x-ratelimit-remaining": "10",
            "x-ratelimit-used": "50",
            "x-ratelimit-reset": "30",
        }
    )
    assert limiter.state.remaining == 10.0
    assert limiter.state.used == 50.0
    assert limiter.state.reset_at is not None


@pytest.mark.asyncio
@respx.mock
async def test_retry_on_429_then_success(settings: Settings, token_payload: dict):
    settings.reddit_max_retries = 3
    respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(200, json=token_payload)
    )
    route = respx.get("https://oauth.reddit.com/search").mock(
        side_effect=[
            Response(429, headers={"Retry-After": "0"}),
            Response(
                200,
                json={"data": {"children": []}},
            ),
        ]
    )
    async with RedditClient(settings) as client:
        payload = await client.get("/search", params={"q": "x"})
    assert payload == {"data": {"children": []}}
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_retry_exhaustion(settings: Settings, token_payload: dict):
    settings.reddit_max_retries = 1
    respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(200, json=token_payload)
    )
    respx.get("https://oauth.reddit.com/search").mock(
        return_value=Response(503, headers={"Retry-After": "0"})
    )
    async with RedditClient(settings) as client:
        with pytest.raises(RedditAPIError):
            await client.get("/search", params={"q": "x"})
