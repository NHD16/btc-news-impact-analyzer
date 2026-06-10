"""Thu thập tin tức bất đồng bộ từ RSS, CryptoPanic, NewsAPI + chấm điểm ưu tiên."""
from __future__ import annotations

import asyncio
import hashlib
import html
import re
import time
from datetime import datetime, timezone

import feedparser
import httpx

from .config import settings
from .models import NewsItem
from .sources import ALL_FEEDS, PRIORITY_KEYWORDS, Feed

USER_AGENT = "Mozilla/5.0 (Market-Analyze BTC News Bot)"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _make_id(title: str, link: str) -> str:
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()[:12]


def _relevance(title: str, summary: str) -> tuple[int, list[str]]:
    text = f" {title} {summary} ".lower()
    score, hits = 0, []
    for kw, weight in PRIORITY_KEYWORDS.items():
        if kw in text:
            score += weight
            hits.append(kw.strip())
    return score, hits


def _entry_time(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def _norm(title, link, summary, source, category, published) -> NewsItem:
    title, summary = _clean(title), _clean(summary)
    score, hits = _relevance(title, summary)
    return NewsItem(
        id=_make_id(title, link or ""), title=title, summary=summary[:400],
        link=link or "", source=source, category=category,
        published=published, relevance=score, keywords=hits,
    )


def _parse_feed(content: bytes, feed: Feed) -> list[NewsItem]:
    """Phân tích RSS (chạy trong thread vì feedparser là blocking)."""
    parsed = feedparser.parse(content)
    out = []
    for e in parsed.entries[:25]:
        out.append(_norm(
            getattr(e, "title", ""), getattr(e, "link", ""),
            getattr(e, "summary", "") or getattr(e, "description", ""),
            feed.name, feed.category, _entry_time(e),
        ))
    return out


# --------------------------------------------------------------------------- RSS
async def _fetch_rss(client: httpx.AsyncClient, feed: Feed) -> list[NewsItem]:
    try:
        r = await client.get(feed.url)
        r.raise_for_status()
        return await asyncio.to_thread(_parse_feed, r.content, feed)
    except Exception as exc:  # noqa: BLE001
        print(f"[RSS] lỗi {feed.name}: {exc}")
        return []


# --------------------------------------------------------------------- CryptoPanic
async def _fetch_cryptopanic(client: httpx.AsyncClient) -> list[NewsItem]:
    if not settings.cryptopanic_api_key:
        return []
    try:
        r = await client.get(
            "https://cryptopanic.com/api/v1/posts/",
            params={"auth_token": settings.cryptopanic_api_key,
                    "currencies": "BTC", "public": "true"},
        )
        r.raise_for_status()
        return [
            _norm(p.get("title", ""), p.get("url", ""), p.get("title", ""),
                  f"CryptoPanic/{p.get('source', {}).get('title', '?')}",
                  "crypto", p.get("published_at", ""))
            for p in r.json().get("results", [])
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"[CryptoPanic] lỗi: {exc}")
        return []


# ------------------------------------------------------------------------ NewsAPI
async def _fetch_newsapi(client: httpx.AsyncClient) -> list[NewsItem]:
    if not settings.newsapi_api_key:
        return []
    try:
        r = await client.get(
            "https://newsapi.org/v2/everything",
            params={"q": "Bitcoin OR Fed OR Trump OR Iran OR interest rate OR crypto",
                    "language": "en", "sortBy": "publishedAt",
                    "pageSize": 40, "apiKey": settings.newsapi_api_key},
        )
        r.raise_for_status()
        return [
            _norm(a.get("title", ""), a.get("url", ""),
                  a.get("description", "") or a.get("content", ""),
                  f"NewsAPI/{(a.get('source') or {}).get('name', '?')}",
                  "macro", a.get("publishedAt", ""))
            for a in r.json().get("articles", [])
        ]
    except Exception as exc:  # noqa: BLE001
        print(f"[NewsAPI] lỗi: {exc}")
        return []


async def collect_all(min_relevance: int = 1) -> list[NewsItem]:
    """Gom song song mọi nguồn, khử trùng lặp, lọc, sắp xếp."""
    async with httpx.AsyncClient(
        timeout=settings.request_timeout,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        tasks = [_fetch_rss(client, f) for f in ALL_FEEDS]
        tasks += [_fetch_cryptopanic(client), _fetch_newsapi(client)]
        results = await asyncio.gather(*tasks)

    raw: list[NewsItem] = [it for group in results for it in group]

    seen: dict[str, NewsItem] = {}
    for it in raw:
        if not it.title or it.relevance < min_relevance:
            continue
        key = re.sub(r"[^a-z0-9]", "", it.title.lower())[:60]
        if key not in seen or it.relevance > seen[key].relevance:
            seen[key] = it

    items = sorted(seen.values(), key=lambda x: (x.relevance, x.published), reverse=True)
    return items[: settings.max_items]
