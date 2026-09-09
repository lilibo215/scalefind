"""Minimal local SQLite storage for short-lived research records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LocalStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_records (
                    reddit_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (reddit_id, kind)
                )
                """
            )
            conn.commit()

    def upsert(
        self,
        reddit_id: str,
        kind: str,
        payload: dict[str, Any],
        *,
        retention_hours: int,
    ) -> None:
        now = _utcnow()
        expires = now + timedelta(hours=retention_hours)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO research_records (reddit_id, kind, payload_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(reddit_id, kind) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at,
                    expires_at=excluded.expires_at
                """,
                (
                    reddit_id,
                    kind,
                    json.dumps(payload, default=str),
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )
            conn.commit()

    def get(self, reddit_id: str, kind: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if kind:
                rows = conn.execute(
                    "SELECT * FROM research_records WHERE reddit_id = ? AND kind = ?",
                    (reddit_id, kind),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM research_records WHERE reddit_id = ?",
                    (reddit_id,),
                ).fetchall()
        return [dict(r) for r in rows]

    def delete_by_id(self, reddit_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM research_records WHERE reddit_id = ?",
                (reddit_id,),
            )
            conn.commit()
            return cur.rowcount

    def delete_search_result(self, reddit_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM research_records WHERE reddit_id = ? AND kind = ?",
                (reddit_id, "search_result"),
            )
            conn.commit()
            return cur.rowcount

    def delete_expired(self, *, now: datetime | None = None) -> int:
        moment = (now or _utcnow()).astimezone(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM research_records WHERE expires_at <= ?",
                (moment,),
            )
            conn.commit()
            return cur.rowcount

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM research_records").fetchone()
        return int(row["c"]) if row else 0
