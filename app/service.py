"""Điều phối một lần chạy: thu thập → phân tích → lưu, kèm phát sự kiện cho SSE."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from . import analyzer, collector, db
from .config import settings
from .models import Notification, RunResult, RunSource

# Trạng thái các run đang sống trong tiến trình (live), phục vụ SSE.
_runs: dict[str, RunResult] = {}
# Mỗi run có một asyncio.Event báo "vừa có cập nhật" để SSE đẩy đi.
_events: dict[str, asyncio.Event] = {}

# Các client đang lắng nghe thông báo "có tin mới" (mỗi client 1 hàng đợi).
_notification_subscribers: set[asyncio.Queue] = set()

MAX_NOTIFY_ITEMS = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_live(run_id: str) -> RunResult | None:
    return _runs.get(run_id)


def _notify(run_id: str) -> None:
    ev = _events.get(run_id)
    if ev:
        ev.set()


def subscribe_notifications() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _notification_subscribers.add(q)
    return q


def unsubscribe_notifications(q: asyncio.Queue) -> None:
    _notification_subscribers.discard(q)


async def _broadcast_notification(note: Notification) -> None:
    for q in list(_notification_subscribers):
        await q.put(note)


async def start_run(min_relevance: int = 3, source: RunSource = "manual") -> str:
    """Tạo run mới, chạy nền, trả về run_id ngay lập tức."""
    run_id = uuid.uuid4().hex[:12]
    run = RunResult(id=run_id, status="running", min_relevance=min_relevance,
                    source=source, started_at=_now())
    _runs[run_id] = run
    _events[run_id] = asyncio.Event()
    await db.save(run)
    asyncio.create_task(_execute(run))
    return run_id


async def _execute(run: RunResult) -> None:
    try:
        prev = await db.latest()
        prev_ids = {it.id for it in prev.items} if prev else None

        items = await collector.collect_all(min_relevance=run.min_relevance)
        analyzed, overall, cost = await analyzer.analyze(items)
        run.items = analyzed
        run.overall = overall
        run.cost_usd = cost
        run.status = "done"

        # Chỉ tính "tin mới" nếu đã có run trước đó (tránh spam ở lần chạy đầu).
        if prev_ids is not None:
            run.new_item_ids = [it.id for it in analyzed if it.id not in prev_ids]
    except Exception as exc:  # noqa: BLE001
        run.status = "error"
        run.error = str(exc)
    finally:
        run.finished_at = _now()
        await db.save(run)
        _notify(run.id)

    if run.status == "done" and run.new_item_ids:
        new_items = [it for it in run.items if it.id in run.new_item_ids]
        note = Notification(
            run_id=run.id, finished_at=run.finished_at, source=run.source,
            new_count=len(new_items), new_items=new_items[:MAX_NOTIFY_ITEMS],
            overall=run.overall,
        )
        await _broadcast_notification(note)


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


async def auto_collect_loop() -> None:
    """Vòng lặp nền: định kỳ tự thu thập & phân tích, phát thông báo nếu có tin mới."""
    while True:
        try:
            await asyncio.sleep(settings.auto_collect_interval_min * 60)
            if not settings.auto_collect_enabled:
                continue
            await start_run(settings.auto_collect_min_relevance, source="auto")
        except asyncio.CancelledError:
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[auto-collect] lỗi: {exc}")
