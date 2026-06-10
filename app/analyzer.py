"""Gọi Claude CLI (agent trên máy) để đánh giá tác động tin tức tới giá BTC."""
from __future__ import annotations

import asyncio
import json
import re

from .config import settings
from .models import AnalyzedItem, Analysis, NewsItem, Overall

SYSTEM = (
    "Bạn là chuyên gia phân tích thị trường crypto. Nhiệm vụ: đánh giá mức độ "
    "tác động của từng tin tức tới GIÁ BITCOIN (BTC) trong ngắn hạn."
)

PROMPT_TEMPLATE = """{system}

Dưới đây là danh sách tin tức (JSON). Với MỖI tin, hãy đánh giá:
- sentiment: "good" (tốt cho BTC), "bad" (xấu cho BTC), hoặc "neutral".
- btc_direction: "up", "down", hoặc "flat" — dự đoán hướng giá BTC.
- impact: "high", "medium", "low" — mức độ ảnh hưởng.
- confidence: số 0-100 — độ tự tin của bạn.
- reason: 1-2 câu tiếng Việt giải thích ngắn gọn.

Sau danh sách, đưa ra một mục "overall":
- bias: "bullish" / "bearish" / "neutral" tổng thể cho BTC.
- summary: 2-3 câu tiếng Việt tóm tắt bức tranh chung.

CHỈ trả về JSON hợp lệ theo đúng cấu trúc sau, KHÔNG thêm chữ nào khác:
{{"items":[{{"id":"...","sentiment":"...","btc_direction":"...","impact":"...","confidence":0,"reason":"..."}}],"overall":{{"bias":"...","summary":"..."}}}}

DỮ LIỆU TIN TỨC:
{news}
"""

_RANK = {"high": 3, "medium": 2, "low": 1}


def _build_payload(items: list[NewsItem]) -> str:
    slim = [{"id": it.id, "source": it.source, "title": it.title,
             "summary": it.summary[:240]} for it in items]
    return json.dumps(slim, ensure_ascii=False, indent=1)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Không tìm thấy JSON trong output của Claude")
    return json.loads(text[start: end + 1])


async def analyze(items: list[NewsItem]) -> tuple[list[AnalyzedItem], Overall, float | None]:
    """Trả về (danh sách tin đã phân tích, đánh giá tổng thể, chi phí USD)."""
    if not items:
        return [], Overall(bias="neutral", summary="Không có tin phù hợp."), None

    prompt = PROMPT_TEMPLATE.format(system=SYSTEM, news=_build_payload(items))

    proc = await asyncio.create_subprocess_exec(
        settings.claude_bin, "-p", prompt, "--output-format", "json",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=settings.claude_timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"Claude CLI quá thời gian ({settings.claude_timeout}s)")

    if proc.returncode != 0:
        raise RuntimeError(f"Claude CLI lỗi (exit {proc.returncode}): {stderr.decode()[:500]}")

    outer = json.loads(stdout.decode())
    parsed = _extract_json(outer.get("result", ""))

    by_id = {a.get("id"): a for a in parsed.get("items", [])}
    merged: list[AnalyzedItem] = []
    for it in items:
        a = by_id.get(it.id, {})
        try:
            analysis = Analysis(**{k: a.get(k) for k in
                                   ("sentiment", "btc_direction", "impact", "confidence", "reason")
                                   if a.get(k) is not None})
        except Exception:  # noqa: BLE001 — Claude trả giá trị lạ → dùng mặc định
            analysis = Analysis(reason="(không phân tích được tin này)")
        merged.append(AnalyzedItem(**it.model_dump(), **analysis.model_dump()))

    merged.sort(key=lambda x: (_RANK.get(x.impact, 0), x.confidence), reverse=True)

    raw_overall = parsed.get("overall", {})
    try:
        overall = Overall(**raw_overall)
    except Exception:  # noqa: BLE001
        overall = Overall(summary=str(raw_overall.get("summary", "")))

    return merged, overall, outer.get("total_cost_usd")
