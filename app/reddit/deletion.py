"""Local research data deletion helpers."""

from __future__ import annotations

import logging

from app.storage.local import LocalStore

logger = logging.getLogger(__name__)


def delete_post_data(store: LocalStore, reddit_id: str) -> int:
    """Delete all locally stored records for a Reddit id."""
    rid = (reddit_id or "").strip()
    if not rid:
        raise ValueError("reddit_id is required")
    deleted = store.delete_by_id(rid)
    logger.info("delete_post_data reddit_id=%s deleted=%s", rid, deleted)
    return deleted


def delete_search_result(store: LocalStore, reddit_id: str) -> int:
    rid = (reddit_id or "").strip()
    if not rid:
        raise ValueError("reddit_id is required")
    deleted = store.delete_search_result(rid)
    logger.info("delete_search_result reddit_id=%s deleted=%s", rid, deleted)
    return deleted


def delete_expired_data(store: LocalStore) -> int:
    deleted = store.delete_expired()
    logger.info("delete_expired_data deleted=%s", deleted)
    return deleted
