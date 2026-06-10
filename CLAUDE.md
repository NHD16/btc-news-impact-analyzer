# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tổng quan dự án

BTC News Impact Analyzer — thu thập tin tức (RSS, CryptoPanic, NewsAPI) từ các nguồn có khả năng ảnh hưởng tới giá Bitcoin (Trump/Truth Social, Fed, SEC, địa chính trị Iran/Israel, crypto media...), chấm điểm độ liên quan, rồi gọi **Claude CLI** (agent đã đăng nhập trên máy, không cần API key riêng) để đánh giá từng tin là tốt/xấu cho BTC và dự đoán hướng giá (up/down/flat).

Stack: **FastAPI (async, Python)** cho backend + **React/Vite** cho frontend, **SQLite** lưu lịch sử các lần phân tích, **SSE** để đẩy kết quả realtime.

## Lệnh thường dùng

### Chạy ứng dụng
```bash
./run.sh                  # tự tạo venv, cài deps, build React, chạy uvicorn ở :8000
```

### Phát triển (hot-reload, 2 server song song)
```bash
./venv/bin/uvicorn app.main:app --reload --port 8000   # backend (tự reload khi sửa app/*.py)
cd frontend && npm run dev                              # frontend Vite :5173, proxy /api → :8000
```
Khi phát triển, **mở http://127.0.0.1:5173** (không phải :8000) — backend :8000 chạy nền chỉ phục vụ API.

### Build frontend cho production
```bash
cd frontend && npm run build    # xuất ra app/static/, FastAPI sẽ phục vụ tại /
```

### Kiểm tra nhanh từng tầng (không cần web)
```bash
./venv/bin/python -c "import asyncio; from app import collector; print(asyncio.run(collector.collect_all(min_relevance=5)))"
```

Không có bộ test tự động trong repo hiện tại.

## Kiến trúc

### Backend (`app/`, package FastAPI)
Luồng xử lý một lần phân tích ("run"):
```
POST /api/runs  →  service.start_run()
   → asyncio task nền:
       collector.collect_all()   # gom song song mọi RSS feed + CryptoPanic + NewsAPI (httpx)
                                  # khử trùng lặp, chấm điểm "relevance" theo PRIORITY_KEYWORDS
       analyzer.analyze()        # gọi `claude -p ... --output-format json` (async subprocess)
                                  # parse JSON: sentiment/btc_direction/impact/confidence/reason mỗi tin
                                  # + overall bias (bullish/bearish/neutral)
       db.save()                 # lưu RunResult (Pydantic) dạng JSON vào SQLite
       service._notify()         # đánh thức asyncio.Event để SSE đẩy update
```
- `service.py` giữ state các run đang chạy trong RAM (`_runs`, `_events`) phục vụ `GET /api/runs/{id}/stream` (SSE). `db.py` là nguồn sự thật lâu dài (SQLite, bảng `runs`, cột `payload` chứa toàn bộ `RunResult` dạng JSON).
- `models.py` là nơi định nghĩa schema dùng xuyên suốt: `NewsItem` (tin thô) + `Analysis` (kết quả Claude) → `AnalyzedItem` (kế thừa cả hai). `RunResult` là toàn bộ kết quả 1 lần chạy; `RunSummary` là bản rút gọn cho danh sách lịch sử.
- `config.py` dùng `pydantic-settings`, đọc `.env` ở project root (`claude_bin`, `claude_timeout`, `max_items`, API keys CryptoPanic/NewsAPI...).
- `sources.py` chứa danh sách `RSS_FEEDS`/`NITTER_FEEDS` và `PRIORITY_KEYWORDS` (từ khóa → trọng số điểm liên quan, ví dụ "trump", "fomc", "iran", "etf"...). Sửa nguồn tin hoặc độ ưu tiên ở đây.
- `analyzer.py` chứa `PROMPT_TEMPLATE` gửi cho Claude — sửa cách đánh giá tin ở đây. Claude phải trả về JSON đúng cấu trúc `{"items":[...], "overall":{...}}`; `_extract_json` xử lý trường hợp Claude bọc trong code fence.
- `main.py`: routes API (`/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/stream`, `/api/runs/latest`, `/api/history`) + mount static React build (`app/static/`) ở `/`. Routes API được khai báo **trước** phần mount static để không bị che.

### Frontend (`frontend/`, React + Vite)
- `api.js` — toàn bộ giao tiếp REST + SSE với backend (qua `EventSource`).
- `useAnalysis.js` — custom hook giữ state (`result`, `history`, `running`, `error`) và điều phối `startRun`/`openRun`.
- `constants.js` / `utils.js` — nhãn hiển thị (DIR/IMPACT/BIAS) và format thời gian/chi phí.
- `components/` — `Header`, `OverallCard` (xu hướng tổng thể), `StatsBar`, `NewsList`/`NewsCard` (từng tin kèm thời điểm xuất bản, hướng giá, độ tự tin), `HistoryList` (click để xem lại run cũ).
- `vite.config.js`: dev server proxy `/api` → `http://127.0.0.1:8000`; `build` xuất ra `../app/static` để FastAPI phục vụ.

### Dữ liệu
- `data/history.db` (SQLite, gitignored) — lịch sử mọi run.
- `app/static/` (gitignored) — bản build React, sinh bởi `npm run build`.

## Lưu ý khi sửa

- Khi thêm trường mới vào `Analysis`/`NewsItem`/`RunResult` (`models.py`), cần đồng bộ cả `analyzer.py` (parse từ Claude) và frontend (`constants.js`, `NewsCard.jsx`).
- `analyzer.analyze()` gọi `claude` CLI thật (tốn phí, ~$0.05–0.15/lần với ~30 tin) — tránh gọi lặp không cần thiết khi test.
- Thêm nguồn RSS mới: thêm `Feed(...)` vào `RSS_FEEDS`/`NITTER_FEEDS` trong `sources.py` (X/Twitter cần proxy qua một instance Nitter vì không có RSS công khai).
