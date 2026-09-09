"""Centralized Reddit API rate limiting and retry helpers."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    remaining: float | None = None
    reset_at: float | None = None
    used: float | None = None


@dataclass
class RateLimiter:
    """Token-bucket style limiter with Reddit header awareness.

    Ensures no uncontrolled concurrency and caps retries with exponential backoff.
    """

    requests_per_minute: int = 60
    max_retries: int = 3
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    _timestamps: deque[float] = field(default_factory=deque)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    state: RateLimitState = field(default_factory=RateLimitState)

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            window = 60.0
            while self._timestamps and now - self._timestamps[0] > window:
                self._timestamps.popleft()

            # Honor Reddit-provided reset if remaining is depleted
            if (
                self.state.remaining is not None
                and self.state.remaining <= 0
                and self.state.reset_at is not None
            ):
                wait = max(0.0, self.state.reset_at - time.time())
                if wait > 0:
                    logger.warning(
                        "rate_limit_wait reason=reddit_headers wait_seconds=%.2f remaining=%s",
                        wait,
                        self.state.remaining,
                    )
                    await asyncio.sleep(min(wait, self.max_backoff_seconds))
                    now = time.monotonic()
                    while self._timestamps and now - self._timestamps[0] > window:
                        self._timestamps.popleft()

            if len(self._timestamps) >= self.requests_per_minute:
                oldest = self._timestamps[0]
                wait = window - (now - oldest)
                logger.warning(
                    "rate_limit_wait reason=local_budget wait_seconds=%.2f rpm=%s",
                    wait,
                    self.requests_per_minute,
                )
                await asyncio.sleep(max(wait, 0.0))
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] > window:
                    self._timestamps.popleft()

            self._timestamps.append(time.monotonic())

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Parse Reddit X-Ratelimit-* headers when present."""
        try:
            remaining = headers.get("x-ratelimit-remaining")
            reset = headers.get("x-ratelimit-reset")
            used = headers.get("x-ratelimit-used")
            if remaining is not None:
                self.state.remaining = float(remaining)
            if used is not None:
                self.state.used = float(used)
            if reset is not None:
                # Reddit provides seconds until reset
                self.state.reset_at = time.time() + float(reset)
            logger.info(
                "rate_limit_state remaining=%s used=%s reset_in=%s",
                remaining,
                used,
                reset,
            )
        except (TypeError, ValueError):
            logger.warning("rate_limit_header_parse_failed")

    def backoff_seconds(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_backoff_seconds)
        delay = self.base_backoff_seconds * (2**attempt)
        return min(delay, self.max_backoff_seconds)

    def should_retry(self, attempt: int, status_code: int) -> bool:
        if attempt >= self.max_retries:
            return False
        return status_code in {429, 500, 502, 503, 504}
