"""Điều phối một lần chạy: thu thập → phân tích → lưu, kèm phát sự kiện cho SSE."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from . import analyzer, collector, db
from .models import RunResult

# Trạng thái các run đang sống trong tiến trình (live), phục vụ SSE.
_runs: dict[str, RunResult] = {}
# Mỗi run có một asyncio.Event báo "vừa có cập nhật" để SSE đẩy đi.
_events: dict[str, asyncio.Event] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_live(run_id: str) -> RunResult | None:
    return _runs.get(run_id)


def _notify(run_id: str) -> None:
    ev = _events.get(run_id)
    if ev:
        ev.set()


async def start_run(min_relevance: int = 3) -> str:
    """Tạo run mới, chạy nền, trả về run_id ngay lập tức."""
    run_id = uuid.uuid4().hex[:12]
    run = RunResult(id=run_id, status="running", min_relevance=min_relevance,
                    started_at=_now())
    _runs[run_id] = run
    _events[run_id] = asyncio.Event()
    await db.save(run)
    asyncio.create_task(_execute(run))
    return run_id


async def _execute(run: RunResult) -> None:
    try:
        items = await collector.collect_all(min_relevance=run.min_relevance)
        analyzed, overall, cost = await analyzer.analyze(items)
        run.items = analyzed
        run.overall = overall
        run.cost_usd = cost
        run.status = "done"
    except Exception as exc:  # noqa: BLE001
        run.status = "error"
        run.error = str(exc)
    finally:
        run.finished_at = _now()
        await db.save(run)
        _notify(run.id)


async def watch(run_id: str):
    """Async generator: yield RunResult mỗi khi run cập nhật, tới khi kết thúc."""
    run = _runs.get(run_id) or await db.get(run_id)
    if run is None:
        return
    yield run
    if run.status != "running":
        return
    ev = _events.get(run_id)
    while True:
        if ev is None:
            return
        await ev.wait()
        ev.clear()
        current = _runs.get(run_id)
        if current is None:
            return
        yield current
        if current.status != "running":
            return
