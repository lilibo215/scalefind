"""Deletion and retention tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.reddit.deletion import delete_expired_data, delete_post_data, delete_search_result
from app.storage.local import LocalStore


def test_delete_post_data(store: LocalStore):
    store.upsert("abc", "post", {"reddit_id": "abc"}, retention_hours=24)
    store.upsert("abc", "comment", {"reddit_id": "abc"}, retention_hours=24)
    deleted = delete_post_data(store, "abc")
    assert deleted == 2
    assert store.get("abc") == []


def test_delete_search_result(store: LocalStore):
    store.upsert("xyz", "search_result", {"reddit_id": "xyz"}, retention_hours=24)
    store.upsert("xyz", "post", {"reddit_id": "xyz"}, retention_hours=24)
    deleted = delete_search_result(store, "xyz")
    assert deleted == 1
    assert len(store.get("xyz")) == 1


def test_delete_expired_data(store: LocalStore, settings: Settings):
    store.upsert("keep", "post", {"reddit_id": "keep"}, retention_hours=24)
    # Insert an already-expired row directly
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    older = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    with store._connect() as conn:
        conn.execute(
            """
            INSERT INTO research_records (reddit_id, kind, payload_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("expired1", "post", '{"reddit_id":"expired1"}', older, past),
        )
        conn.commit()

    assert store.count() == 2
    deleted = delete_expired_data(store)
    assert deleted == 1
    assert store.count() == 1
    assert store.get("keep")
    assert store.get("expired1") == []


def test_retention_default_is_short(settings: Settings):
    assert settings.data_retention_hours == 24
