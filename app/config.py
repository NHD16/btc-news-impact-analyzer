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

    # CSDL
    db_path: str = str(DATA_DIR / "history.db")


settings = Settings()
