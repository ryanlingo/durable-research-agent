"""Simple SQLite-backed checkpoint store for the non-Temporal agent."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "checkpoints.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def save_state(run_id: str, state: dict[str, Any]) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO runs (run_id, state_json) VALUES (?, ?)",
        (run_id, json.dumps(state)),
    )
    conn.commit()
    conn.close()


def load_state(run_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute(
        "SELECT state_json FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row[0])


def set_approval(run_id: str, status: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO approvals (run_id, status) VALUES (?, ?)",
        (run_id, status),
    )
    conn.commit()
    conn.close()


def get_approval(run_id: str) -> str:
    conn = _connect()
    row = conn.execute(
        "SELECT status FROM approvals WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else "pending"
