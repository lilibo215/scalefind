"""Read-only Reddit HTTP client. All Reddit network I/O goes through here."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

import httpx

from app.config import Settings
from app.reddit.auth import AccessToken, CredentialError, fetch_app_only_token, require_credentials
from app.reddit.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

OAUTH_BASE = "https://oauth.reddit.com"

# Methods that must never be exposed as write helpers on this client.
FORBIDDEN_WRITE_METHOD_NAMES = frozenset(
    {
        "submit",
        "comment",
        "reply",
        "vote",
        "save",
        "unsave",
        "subscribe",
        "unsubscribe",
        "send_message",
        "compose",
        "follow",
        "unfollow",
        "moderate",
        "approve",
        "remove",
        "ban",
        "edit",
        "delete_thing",
    }
)


class RedditAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, category: str = "api_error"):
        super().__init__(message)
        self.status_code = status_code
        self.category = category


class RedditClient:
    """Minimal read-only Reddit API client."""

    def __init__(self, settings: Settings, rate_limiter: RateLimiter | None = None):
        require_credentials(settings)
        self.settings = settings
        self.rate_limiter = rate_limiter or RateLimiter(
            requests_per_minute=settings.reddit_rate_limit_requests_per_minute,
            max_retries=settings.reddit_max_retries,
        )
        self._token: AccessToken | None = None
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> RedditClient:
        self._http = httpx.AsyncClient(
            base_url=OAUTH_BASE,
            timeout=self.settings.reddit_request_timeout_seconds,
            headers={"User-Agent": self.settings.reddit_user_agent},
        )
        self._token = await fetch_app_only_token(self.settings, client=self._http)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def ensure_token(self) -> AccessToken:
        if self._token is None:
            if self._http is None:
                raise CredentialError("Reddit client HTTP session is not open")
            self._token = await fetch_app_only_token(self.settings, client=self._http)
        return self._token

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        method_u = method.upper()
        if method_u not in {"GET", "HEAD"}:
            raise RedditAPIError(
                "Write operations are not permitted in this read-only prototype",
                category="read_only_violation",
            )

        if self._http is None:
            raise RedditAPIError("Reddit client is not initialized", category="client_state")

        request_id = uuid.uuid4().hex[:12]
        attempt = 0
        while True:
            await self.rate_limiter.acquire()
            token = await self.ensure_token()
            started = time.perf_counter()
            response = await self._http.request(
                method_u,
                path,
                params=params,
                headers={"Authorization": token.authorization_header()},
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            self.rate_limiter.update_from_headers({k.lower(): v for k, v in response.headers.items()})

            logger.info(
                "reddit_request id=%s method=%s path=%s status=%s latency_ms=%s attempt=%s",
                request_id,
                method_u,
                path,
                response.status_code,
                latency_ms,
                attempt,
            )

            if response.status_code == 401 and attempt == 0:
                # Refresh token once
                self._token = None
                attempt += 1
                continue

            if self.rate_limiter.should_retry(attempt, response.status_code):
                retry_after_raw = response.headers.get("Retry-After")
                retry_after = float(retry_after_raw) if retry_after_raw else None
                delay = self.rate_limiter.backoff_seconds(attempt, retry_after)
                logger.warning(
                    "reddit_retry id=%s status=%s delay_seconds=%.2f attempt=%s",
                    request_id,
                    response.status_code,
                    delay,
                    attempt,
                )
                await asyncio.sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 400:
                raise RedditAPIError(
                    f"Reddit API error status={response.status_code}",
                    status_code=response.status_code,
                    category="http_error",
                )

            if not response.content:
                return {}
            return response.json()

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        return await self.request("GET", path, params=params)
