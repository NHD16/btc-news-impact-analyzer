"""Định nghĩa nguồn tin và từ khóa ưu tiên."""
from __future__ import annotations

from pydantic import BaseModel


class Feed(BaseModel):
    name: str
    url: str
    category: str  # "social" | "macro" | "crypto"


# ---------------------------------------------------------------------------
# Nguồn RSS miễn phí.
# ---------------------------------------------------------------------------
RSS_FEEDS: list[Feed] = [
    # --- Nhân vật / tổ chức ảnh hưởng ---
    Feed(name="Trump (Truth Social)", url="https://trumpstruth.org/feed", category="social"),
    Feed(name="Fed - Press Releases", url="https://www.federalreserve.gov/feeds/press_all.xml", category="social"),
    Feed(name="Fed - Speeches", url="https://www.federalreserve.gov/feeds/speeches.xml", category="social"),
    Feed(name="SEC - Press", url="https://www.sec.gov/news/pressreleases.rss", category="social"),

    # --- Vĩ mô / địa chính trị ---
    Feed(name="Al Jazeera (World)", url="https://www.aljazeera.com/xml/rss/all.xml", category="macro"),
    Feed(name="BBC World", url="http://feeds.bbci.co.uk/news/world/rss.xml", category="macro"),
    Feed(name="CNBC - Economy", url="https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", category="macro"),
    Feed(name="MarketWatch", url="https://feeds.content.dowjones.io/public/rss/mw_topstories", category="macro"),

    # --- Crypto ---
    Feed(name="CoinDesk", url="https://www.coindesk.com/arc/outboundfeeds/rss/", category="crypto"),
    Feed(name="Cointelegraph", url="https://cointelegraph.com/rss", category="crypto"),
    Feed(name="Bitcoin Magazine", url="https://bitcoinmagazine.com/.rss/full/", category="crypto"),
    Feed(name="Decrypt", url="https://decrypt.co/feed", category="crypto"),
    Feed(name="NewsBTC", url="https://www.newsbtc.com/feed/", category="crypto"),
    Feed(name="BeInCrypto", url="https://beincrypto.com/feed/", category="crypto"),
    Feed(name="AMBCrypto", url="https://ambcrypto.com/feed/", category="crypto"),
    Feed(name="Crypto Briefing", url="https://cryptobriefing.com/feed/", category="crypto"),
]

# Tài khoản X (Twitter) qua Nitter self-hosted.
# Đặt NITTER_BASE_URL trong .env (vd: https://nitter.yourdomain.com) để kích hoạt.
# Các instance Nitter công khai gần như không còn hoạt động từ 2024.
_NITTER_ACCOUNTS: list[tuple[str, str, str]] = [
    ("Reuters", "Reuters", "macro"),
    ("AP Breaking News", "APBreaking", "macro"),
    ("Watcher Guru", "WatcherGuru", "crypto"),
    ("Bitcoin Archive", "BTC_Archive", "crypto"),
    ("Michael Saylor", "saylor", "crypto"),
    ("Documenting Bitcoin", "DocumentingBTC", "crypto"),
    ("Walter Bloomberg", "DeItaone", "macro"),
]


def _build_nitter_feeds() -> list[Feed]:
    from .config import settings
    base = settings.nitter_base_url.rstrip("/")
    if not base:
        return []
    return [
        Feed(name=f"{name} (X)", url=f"{base}/{handle}/rss", category=cat)
        for name, handle, cat in _NITTER_ACCOUNTS
    ]


NITTER_FEEDS: list[Feed] = _build_nitter_feeds()

ALL_FEEDS = RSS_FEEDS + NITTER_FEEDS

# ---------------------------------------------------------------------------
# Từ khóa ưu tiên — tin chứa các từ này được nâng điểm "relevance".
# ---------------------------------------------------------------------------
PRIORITY_KEYWORDS: dict[str, int] = {
    # Nhân vật / tổ chức
    "trump": 5, "powell": 5, "federal reserve": 5, "fed ": 5, "fomc": 5,
    "sec ": 4, "blackrock": 4, "elon musk": 3, "treasury": 3, "yellen": 3,
    "biden": 2, "white house": 3,
    # Chính sách tiền tệ
    "interest rate": 5, "rate cut": 5, "rate hike": 5, "inflation": 4,
    "cpi": 4, "quantitative": 4, "tariff": 4, "recession": 4,
    # Crypto cụ thể
    "bitcoin": 5, "btc": 5, "etf": 5, "crypto": 3, "stablecoin": 3,
    "spot etf": 5, "halving": 4, "binance": 3, "coinbase": 3,
    # Địa chính trị / chiến tranh
    "iran": 5, "israel": 4, "war": 4, "strike": 3, "sanction": 4,
    "russia": 3, "ukraine": 3, "china": 3, "nuclear": 4, "conflict": 3,
    "geopolitical": 3, "oil price": 3,
}
