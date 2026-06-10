# ₿ BTC News Impact Analyzer

Tool thu thập tin tức từ các sự kiện lớn trên thế giới có thể ảnh hưởng tới giá **Bitcoin (BTC)**, ưu tiên nguồn từ người/tổ chức có ảnh hưởng (Trump, Fed, chiến tranh Iran, SEC, ETF...), sau đó dùng **Claude (agent trên máy)** để đánh giá tin **tốt/xấu** và dự đoán **BTC tăng/giảm**. Kết quả hiển thị trên **giao diện web** kèm **thời điểm tin xuất hiện** và **lịch sử phân tích**.

> Phiên bản 2.0 — backend **FastAPI** (async) + frontend **React (Vite)**, cập nhật realtime qua **SSE**, lưu lịch sử bằng **SQLite**.

## Cách chạy nhanh

```bash
./run.sh
```

Mở **http://127.0.0.1:8000** → bấm **🔄 Thu thập & Phân tích**.
Tài liệu API tự sinh tại **http://127.0.0.1:8000/docs**.

> Lần đầu chạy `run.sh` sẽ tự tạo venv, cài thư viện Python, **build React**, và tạo file `.env`.

## Kiến trúc

```
Market_Analyze/
├── app/                    # BACKEND — gói FastAPI
│   ├── main.py             # app + routes + phục vụ React build
│   ├── config.py           # cấu hình (pydantic-settings, đọc .env)
│   ├── models.py           # Pydantic schemas (NewsItem, Analysis, RunResult...)
│   ├── sources.py          # định nghĩa nguồn RSS + từ khóa ưu tiên
│   ├── collector.py        # thu thập tin BẤT ĐỒNG BỘ (httpx + feedparser)
│   ├── analyzer.py         # gọi Claude CLI (async subprocess) đánh giá
│   ├── service.py          # điều phối run + phát sự kiện cho SSE
│   ├── db.py               # lưu lịch sử bằng SQLite
│   └── static/             # bản build React (vite build → tự sinh)
│
├── frontend/               # FRONTEND — React + Vite
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js      # dev proxy /api → :8000, build → app/static
│   └── src/
│       ├── main.jsx        # điểm vào React
│       ├── App.jsx         # bố cục trang
│       ├── api.js          # lớp gọi API + SSE
│       ├── useAnalysis.js  # custom hook quản lý state
│       ├── constants.js    # nhãn hiển thị (DIR/IMPACT/BIAS)
│       ├── utils.js        # định dạng thời gian, chi phí
│       ├── index.css       # giao diện
│       └── components/
│           ├── Header.jsx
│           ├── OverallCard.jsx
│           ├── StatsBar.jsx
│           ├── NewsList.jsx
│           ├── NewsCard.jsx
│           └── HistoryList.jsx
│
├── data/                   # CSDL SQLite (tự tạo)
├── requirements.txt
├── run.sh
└── .env.example
```

## Phát triển frontend (hot-reload)

Chạy backend và frontend riêng để có hot-reload khi sửa React:

```bash
# Terminal 1 — backend
./venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (Vite dev, proxy /api về :8000)
cd frontend && npm run dev      # → http://127.0.0.1:5173
```

Khi xong, build để FastAPI phục vụ ở production:
```bash
cd frontend && npm run build    # xuất ra app/static/
```

Luồng xử lý:

```
POST /api/runs  →  service.start_run()  →  chạy nền:
     collector.collect_all()  (gom song song mọi nguồn, chấm điểm ưu tiên)
        ↓
     analyzer.analyze()       (gửi Claude CLI → JSON: tốt/xấu, BTC ▲▼, tác động)
        ↓
     db.save()                (lưu vào SQLite)
        ↓
  GET /api/runs/{id}/stream   →  SSE đẩy trạng thái realtime về trình duyệt
```

## Các endpoint chính

| Method | Đường dẫn | Mô tả |
|--------|-----------|-------|
| GET  | `/` | Giao diện web dashboard |
| POST | `/api/runs?min_relevance=3` | Bắt đầu một lần thu thập & phân tích |
| GET  | `/api/runs/{id}` | Trạng thái + kết quả một run |
| GET  | `/api/runs/{id}/stream` | SSE — cập nhật realtime tới khi xong |
| GET  | `/api/runs/latest` | Run hoàn tất gần nhất |
| GET  | `/api/history?limit=20` | Lịch sử các lần phân tích |
| GET  | `/docs` | API docs (Swagger UI tự sinh) |

## Nguồn dữ liệu

| Nhóm | Nguồn mặc định |
|------|----------------|
| Nhân vật/tổ chức | **Trump (Truth Social)**, **Fed** (press + speeches), **SEC** |
| Vĩ mô / địa chính trị | Al Jazeera, BBC World, CNBC Economy (chiến tranh Iran, lãi suất...) |
| Crypto | CoinDesk, Cointelegraph, Bitcoin Magazine |
| API (tùy chọn) | CryptoPanic, NewsAPI.org |

### Thêm tài khoản X (Twitter)
X không có RSS công khai. Mở `app/sources.py`, thêm vào `NITTER_FEEDS` một instance Nitter:
```python
NITTER_FEEDS = [
    Feed(name="Elon Musk (X)", url="https://nitter.net/elonmusk/rss", category="social"),
]
```

### API key (tùy chọn)
Mở `.env` và điền nếu muốn nhiều tin hơn:
```
CRYPTOPANIC_API_KEY=...   # https://cryptopanic.com/developers/api/
NEWSAPI_API_KEY=...        # https://newsapi.org/
```
Để trống vẫn chạy được nhờ nguồn RSS miễn phí.

## Tùy chỉnh

| File | Sửa gì |
|------|--------|
| `app/sources.py` | Nguồn RSS, từ khóa ưu tiên + trọng số |
| `app/config.py` | `max_items`, timeout, đường dẫn DB |
| `app/analyzer.py` | Prompt phân tích gửi cho Claude |
| `frontend/src/` | Giao diện React (sửa xong nhớ `npm run build`) |

## Lưu ý

- Mỗi lần phân tích tốn một khoản phí Claude nhỏ (hiển thị cuối trang, thường ~$0.1).
- Đây là công cụ hỗ trợ tham khảo — **không phải lời khuyên đầu tư**.
- Đánh giá dùng đúng Claude bạn đã đăng nhập trong Claude Code (không cần API key Anthropic riêng).

## Hướng phát triển tiếp (gợi ý)

- Chạy định kỳ tự động (APScheduler) → phân tích mỗi 30 phút.
- Thêm biểu đồ giá BTC realtime để đối chiếu dự đoán.
- Bảng so sánh độ chính xác dự đoán theo thời gian (dùng dữ liệu lịch sử đã lưu).
