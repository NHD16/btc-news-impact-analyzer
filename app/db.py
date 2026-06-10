"""Lưu trữ lịch sử các lần phân tích bằng SQLite (stdlib)."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import closing

from .config import settings
from .models import RunResult, RunSummary

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id            TEXT PRIMARY KEY,
    status        TEXT NOT NULL,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    min_relevance INTEGER,
    source        TEXT DEFAULT 'manual',
    bias          TEXT,
    summary       TEXT,
    cost_usd      REAL,
    item_count    INTEGER DEFAULT 0,
    error         TEXT,
    payload       TEXT          -- toàn bộ RunResult dạng JSON
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with closing(_connect()) as conn:
        conn.executescript(_SCHEMA)
        try:
            conn.execute("ALTER TABLE runs ADD COLUMN source TEXT DEFAULT 'manual'")
        except sqlite3.OperationalError:
            pass  # cột đã tồn tại (CSDL cũ)
        conn.commit()


def _save_sync(run: RunResult) -> None:
    with closing(_connect()) as conn:
        conn.execute(
            """INSERT INTO runs (id, status, started_at, finished_at, min_relevance,
                                 source, bias, summary, cost_usd, item_count, error, payload)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 status=excluded.status, finished_at=excluded.finished_at,
                 bias=excluded.bias, summary=excluded.summary,
                 cost_usd=excluded.cost_usd, item_count=excluded.item_count,
                 error=excluded.error, payload=excluded.payload""",
            (run.id, run.status, run.started_at, run.finished_at, run.min_relevance,
             run.source, run.overall.bias, run.overall.summary, run.cost_usd,
             len(run.items), run.error, run.model_dump_json()),
        )
        conn.commit()


def _get_sync(run_id: str) -> RunResult | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
    return RunResult.model_validate_json(row["payload"]) if row else None


def _latest_sync() -> RunResult | None:
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT payload FROM runs WHERE status='done' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
    return RunResult.model_validate_json(row["payload"]) if row else None


def _history_sync(limit: int) -> list[RunSummary]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            """SELECT id, status, started_at, finished_at, source, bias, item_count, cost_usd
               FROM runs ORDER BY started_at DESC LIMIT ?""", (limit,),
        ).fetchall()
    return [
        RunSummary(
            id=r["id"], status=r["status"], started_at=r["started_at"],
            finished_at=r["finished_at"], source=r["source"] or "manual",
            bias=r["bias"] or "neutral",
            item_count=r["item_count"] or 0, cost_usd=r["cost_usd"],
        )
        for r in rows
    ]


# --- API async (chạy SQLite trong thread để không chặn event loop) ---
async def save(run: RunResult) -> None:
    await asyncio.to_thread(_save_sync, run)


async def get(run_id: str) -> RunResult | None:
    return await asyncio.to_thread(_get_sync, run_id)


async def latest() -> RunResult | None:
    return await asyncio.to_thread(_latest_sync)


async def history(limit: int = 20) -> list[RunSummary]:
    return await asyncio.to_thread(_history_sync, limit)
