"""Gửi thông báo "có tin mới" ra Discord/Telegram (qua webhook/bot API)."""
from __future__ import annotations

import httpx

from .config import settings
from .models import Notification

_DIR_LABEL = {"up": "BTC ▲ TĂNG", "down": "BTC ▼ GIẢM", "flat": "BTC ◆ ĐI NGANG"}
_BIAS_LABEL = {"bullish": "BULLISH 🐂", "bearish": "BEARISH 🐻", "neutral": "NEUTRAL"}


def _format_message(note: Notification) -> str:
    lines = [
        f"📰 **{note.new_count} tin mới** "
        f"({'tự động' if note.source == 'auto' else 'thủ công'}) — "
        f"Tổng quan: {_BIAS_LABEL.get(note.overall.bias, note.overall.bias)}",
    ]
    if note.overall.summary:
        lines.append(note.overall.summary)
    lines.append("")
    for it in note.new_items:
        dir_label = _DIR_LABEL.get(it.btc_direction, it.btc_direction)
        lines.append(f"• [{dir_label}] {it.title}")
        if it.link:
            lines.append(f"  {it.link}")
    return "\n".join(lines)


async def _send_discord(client: httpx.AsyncClient, message: str) -> None:
    try:
        await client.post(settings.discord_webhook_url, json={"content": message[:2000]})
    except Exception as exc:  # noqa: BLE001
        print(f"[notifier] lỗi gửi Discord: {exc}")


async def _send_telegram(client: httpx.AsyncClient, message: str) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message[:4096],
        "disable_web_page_preview": True,
    }
    try:
        await client.post(url, json=payload)
    except Exception as exc:  # noqa: BLE001
        print(f"[notifier] lỗi gửi Telegram: {exc}")


async def notify_external(note: Notification) -> None:
    """Gửi thông báo tin mới tới Discord/Telegram nếu đã cấu hình."""
    if not settings.discord_webhook_url and not (
        settings.telegram_bot_token and settings.telegram_chat_id
    ):
        return

    message = _format_message(note)
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        if settings.discord_webhook_url:
            await _send_discord(client, message)
        if settings.telegram_bot_token and settings.telegram_chat_id:
            await _send_telegram(client, message)
