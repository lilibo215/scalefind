"""Authentication and credential tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from app.config import Settings
from app.reddit.auth import CredentialError, fetch_app_only_token, require_credentials


def test_missing_credentials_fail_safely():
    settings = Settings(REDDIT_CLIENT_ID="", REDDIT_CLIENT_SECRET="")
    with pytest.raises(CredentialError):
        require_credentials(settings)


def test_partial_credentials_fail_safely():
    settings = Settings(REDDIT_CLIENT_ID="only-id", REDDIT_CLIENT_SECRET="")
    assert settings.credentials_present() is False
    with pytest.raises(CredentialError):
        require_credentials(settings)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_app_only_token_success(settings: Settings, token_payload: dict):
    route = respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(200, json=token_payload)
    )
    token = await fetch_app_only_token(settings)
    assert route.called
    assert token.access_token == "secret-access-token-value"
    assert token.token_type == "bearer"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_app_only_token_http_error(settings: Settings):
    respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(401, json={"error": "invalid_client"})
    )
    with pytest.raises(CredentialError):
        await fetch_app_only_token(settings)
