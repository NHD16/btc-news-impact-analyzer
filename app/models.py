"""Pydantic schemas dùng chung cho thu thập, phân tích và API."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["good", "bad", "neutral"]
Direction = Literal["up", "down", "flat"]
Impact = Literal["high", "medium", "low"]
Bias = Literal["bullish", "bearish", "neutral"]
RunStatus = Literal["running", "done", "error"]


class NewsItem(BaseModel):
    """Một tin thô đã thu thập."""
    id: str
    title: str
    summary: str = ""
    link: str = ""
    source: str
    category: str
    published: str  # ISO 8601
    relevance: int = 0
    keywords: list[str] = Field(default_factory=list)


class Analysis(BaseModel):
    """Kết quả Claude đánh giá cho một tin."""
    sentiment: Sentiment = "neutral"
    btc_direction: Direction = "flat"
    impact: Impact = "low"
    confidence: int = 0
    reason: str = ""


class AnalyzedItem(NewsItem, Analysis):
    """Tin đã gắn kết quả phân tích."""


class Overall(BaseModel):
    bias: Bias = "neutral"
    summary: str = ""


class RunResult(BaseModel):
    """Một lần chạy phân tích hoàn chỉnh."""
    id: str
    status: RunStatus = "running"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None
    min_relevance: int = 3
    items: list[AnalyzedItem] = Field(default_factory=list)
    overall: Overall = Field(default_factory=Overall)
    cost_usd: float | None = None
    error: str | None = None


class RunSummary(BaseModel):
    """Bản tóm tắt một run (cho danh sách lịch sử)."""
    id: str
    status: RunStatus
    started_at: str
    finished_at: str | None
    bias: Bias
    item_count: int
    cost_usd: float | None
