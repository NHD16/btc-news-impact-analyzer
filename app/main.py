"""FastAPI app — dashboard phân tích tác động tin tức tới giá BTC."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import db, service
from .models import RunResult, RunSummary

# Thư mục chứa bản build React (vite build → app/static).
STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    yield


app = FastAPI(title="BTC News Impact Analyzer", version="2.0.0", lifespan=lifespan)


@app.post("/api/runs")
async def create_run(min_relevance: int = Query(3, ge=1, le=20)):
    run_id = await service.start_run(min_relevance)
    return {"run_id": run_id}


@app.get("/api/runs/latest", response_model=RunResult | None)
async def latest_run():
    return await db.latest()


@app.get("/api/runs/{run_id}", response_model=RunResult)
async def get_run(run_id: str):
    run = service.get_live(run_id) or await db.get(run_id)
    if run is None:
        raise HTTPException(404, "Không tìm thấy run")
    return run


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str):
    """Server-Sent Events: đẩy trạng thái run tới khi hoàn tất."""
    async def gen():
        async for run in service.watch(run_id):
            yield f"data: {run.model_dump_json()}\n\n"
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/history", response_model=list[RunSummary])
async def get_history(limit: int = Query(20, ge=1, le=100)):
    return await db.history(limit)


# --- Phục vụ giao diện React đã build (sau cùng để không chặn /api/*) ---
if (STATIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")


@app.get("/")
async def index():
    if INDEX_HTML.is_file():
        return FileResponse(INDEX_HTML)
    return JSONResponse(
        {"message": "Chưa build giao diện. Chạy: cd frontend && npm install && npm run build "
                    "(hoặc npm run dev để phát triển)."},
        status_code=503,
    )
