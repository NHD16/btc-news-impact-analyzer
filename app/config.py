"""Cấu hình ứng dụng (đọc từ biến môi trường / file .env)."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # API key (tùy chọn)
    cryptopanic_api_key: str = ""
    newsapi_api_key: str = ""

    # Claude CLI
    claude_bin: str = "claude"
    claude_timeout: int = 300  # giây

    # Thu thập
    max_items: int = 30
    request_timeout: float = 20.0

    # Tự động thu thập định kỳ + thông báo tin mới
    auto_collect_enabled: bool = True
    auto_collect_interval_min: int = 60
    auto_collect_min_relevance: int = 5

    # Nitter self-hosted (để trống nếu không có)
    nitter_base_url: str = ""

    # Thông báo ra ngoài (tùy chọn)
    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # CSDL
    db_path: str = str(DATA_DIR / "history.db")


settings = Settings()
