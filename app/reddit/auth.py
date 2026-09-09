"""Reddit OAuth authentication (application-only / client credentials)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.logging_utils import redact_mapping

logger = logging.getLogger(__name__)

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"


class CredentialError(RuntimeError):
    """Raised when Reddit credentials are missing or invalid for startup use."""


@dataclass
class AccessToken:
    access_token: str
    token_type: str
    expires_in: int
    scope: str | None = None

    def authorization_header(self) -> str:
        return f"{self.token_type} {self.access_token}"


def require_credentials(settings: Settings) -> None:
    if not settings.credentials_present():
        raise CredentialError(
            "Reddit credentials missing. Set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET in the environment."
        )


async def fetch_app_only_token(
    settings: Settings,
    client: httpx.AsyncClient | None = None,
) -> AccessToken:
    """Obtain an application-only OAuth token for read-only public data access.

    Uses the client_credentials grant. Never logs secrets or tokens.
    """
    require_credentials(settings)

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=settings.reddit_request_timeout_seconds)

    try:
        response = await client.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
            headers={"User-Agent": settings.reddit_user_agent},
        )
        logger.info(
            "reddit_auth status=%s latency_hint=token_request",
            response.status_code,
        )
        if response.status_code >= 400:
            # Do not include response body — may contain sensitive details
            raise CredentialError(
                f"Reddit authentication failed with status {response.status_code}"
            )
        payload: dict[str, Any] = response.json()
        token = payload.get("access_token")
        if not token:
            raise CredentialError("Reddit authentication response missing access_token")
        return AccessToken(
            access_token=str(token),
            token_type=str(payload.get("token_type", "bearer")),
            expires_in=int(payload.get("expires_in", 3600)),
            scope=payload.get("scope"),
        )
    finally:
        if owns_client:
            await client.aclose()


def safe_auth_log_context(**kwargs: Any) -> dict[str, Any]:
    """Helper for tests and callers that need redacted auth context."""
    return redact_mapping(kwargs)
