#!/usr/bin/env bash
# Chạy nhanh BTC News Impact Analyzer (FastAPI + React)
set -e
cd "$(dirname "$0")"

# --- Backend: venv + dependencies ---
if [ ! -d venv ]; then
  echo "📦 Tạo môi trường ảo Python & cài dependencies..."
  python3 -m venv venv
  ./venv/bin/pip install -q --upgrade pip
  ./venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "ℹ️  Đã tạo .env (bạn có thể thêm API key CryptoPanic/NewsAPI nếu muốn)."
fi

# --- Frontend: build React nếu chưa có ---
if [ ! -f app/static/index.html ]; then
  echo "⚛️  Build giao diện React..."
  (cd frontend && npm install && npm run build)
fi

echo "🚀 Khởi động web server tại http://127.0.0.1:8000"
exec ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 "$@"
