"""Read-only enforcement and credential redaction tests."""

from __future__ import annotations

import inspect
import logging

import pytest

from app.logging_utils import RedactingFilter, redact_mapping, redact_text
from app.reddit import client as client_module
from app.reddit.client import FORBIDDEN_WRITE_METHOD_NAMES, RedditAPIError, RedditClient
from app.config import Settings


def test_forbidden_write_methods_not_on_client():
    members = {
        name
        for name, _ in inspect.getmembers(RedditClient, predicate=inspect.isfunction)
    }
    members |= set(dir(RedditClient))
    overlap = FORBIDDEN_WRITE_METHOD_NAMES & members
    assert not overlap, f"Write methods must not exist on RedditClient: {overlap}"


def test_write_method_registry_is_enforced():
    """Fails if a developer adds a write helper matching the forbidden list."""
    source = inspect.getsource(client_module)
    for name in FORBIDDEN_WRITE_METHOD_NAMES:
        # Detect method definitions like `def submit(` or `async def vote(`
        assert f"def {name}(" not in source
        assert f"async def {name}(" not in source


@pytest.mark.asyncio
async def test_client_rejects_non_get(settings: Settings):
    # Bypass network by constructing client and calling request directly with a stub http
    client = RedditClient(settings)
    client._http = object()  # type: ignore[assignment]
    client._token = type("T", (), {"authorization_header": lambda self: "bearer x"})()  # type: ignore[assignment]
    with pytest.raises(RedditAPIError) as exc:
        await client.request("POST", "/api/submit")
    assert exc.value.category == "read_only_violation"


def test_redact_text_removes_tokens():
    text = "access_token=secret-access-token-value bearer abc.def.ghi"
    redacted = redact_text(text)
    assert "secret-access-token-value" not in redacted
    assert "abc.def.ghi" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_mapping_sensitive_keys():
    data = {
        "client_secret": "super-secret",
        "access_token": "tok",
        "refresh_token": "ref",
        "authorization_code": "code123",
        "endpoint": "/search",
    }
    out = redact_mapping(data)
    assert out["client_secret"] == "[REDACTED]"
    assert out["access_token"] == "[REDACTED]"
    assert out["refresh_token"] == "[REDACTED]"
    assert out["authorization_code"] == "[REDACTED]"
    assert out["endpoint"] == "/search"


def test_logging_filter_redacts(caplog):
    logger = logging.getLogger("test_redaction_logger")
    logger.setLevel(logging.INFO)
    logger.addFilter(RedactingFilter())
    with caplog.at_level(logging.INFO, logger="test_redaction_logger"):
        logger.info("client_secret=shh access_token=tok123")
    combined = " ".join(r.getMessage() for r in caplog.records)
    assert "shh" not in combined
    assert "tok123" not in combined
    assert "[REDACTED]" in combined
