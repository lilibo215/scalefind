"""Safe logging helpers that redact OAuth secrets and tokens."""

from __future__ import annotations

import logging
import re
from typing import Any

SENSITIVE_KEYS = (
    "client_secret",
    "access_token",
    "refresh_token",
    "authorization_code",
    "code",
    "password",
    "token",
)

_TOKEN_RE = re.compile(
    r"(?i)(client_secret|access_token|refresh_token|authorization_code|bearer)\s*[:=]\s*\S+"
)
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")


def redact_text(value: str) -> str:
    """Remove credential-like substrings from free-form text."""
    redacted = _TOKEN_RE.sub(r"\1=[REDACTED]", value)
    redacted = _BEARER_RE.sub("Bearer [REDACTED]", redacted)
    return redacted


def redact_mapping(data: dict[str, Any] | None) -> dict[str, Any]:
    """Return a shallow copy with sensitive keys redacted."""
    if not data:
        return {}
    out: dict[str, Any] = {}
    for key, value in data.items():
        key_l = str(key).lower()
        if any(s in key_l for s in SENSITIVE_KEYS):
            out[key] = "[REDACTED]"
        elif isinstance(value, str):
            out[key] = redact_text(value)
        else:
            out[key] = value
    return out


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_mapping(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_text(a) if isinstance(a, str) else a for a in record.args
                )
        return True


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
    root.setLevel(level)
    for handler in root.handlers:
        handler.addFilter(RedactingFilter())
    # Ensure package loggers inherit the filter
    for name in ("app", "uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).addFilter(RedactingFilter())
