"""Trend engine — keyless sources: Google News RSS + Google Trends RSS.

Every channel declares a trends.mode:
  - "news"    : script topic = fresh headlines (tech / money channels)
  - "trends"  : pick one daily trending search (facts channel)
  - "theme"   : evergreen daily theme, optionally flavored by news (mindset channel)

All fetchers degrade gracefully: any failure returns empty lists and the
pipeline falls back to the offline content banks.
"""
from __future__ import annotations

import datetime
import random

import feedparser
import requests

from . import history
from .utils import log

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
TIMEOUT = 15


def _get(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        if r.status_code == 200 and len(r.content) > 500:
            return r.text
        log(f"   ⚠ {url[:60]} → status {r.status_code}")
    except Exception as e:
        log(f"   ⚠ {url[:60]} → {type(e).__name__}")
    return None


def news_headlines(query: str, limit: int = 6) -> list[str]:
    """Google News RSS search; 'when:2d' keeps results fresh."""
    url = (
        "https://news.google.com/rss/search?q="
        + requests.utils.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    xml = _get(url)
    if not xml:
        return []
    feed = feedparser.parse(xml)
    out = []
    for e in feed.entries[: limit + 4]:
        title = e.get("title", "").strip()
        # strip trailing " - Publisher"
        if " - " in title:
            title = title.rsplit(" - ", 1)[0].strip()
        if 25 < len(title) < 160 and title not in out:
            out.append(title)
        if len(out) >= limit:
            break
    return out


def trending_searches(geo: str = "US", limit: int = 20) -> list[str]:
    """Google Trends daily trending searches (keyless RSS)."""
    xml = _get(f"https://trends.google.com/trending/rss?geo={geo}")
    if not xml:
        return []
    feed = feedparser.parse(xml)
    out = []
    for e in feed.entries[:limit]:
        title = e.get("title", "").strip()
        if 3 < len(title) < 60:
            out.append(title)
    return out


def pick_topic(cfg: dict, rng: random.Random, slot: int = 1) -> dict:
    """Return {'topic': str, 'source': str, 'headlines': [str, ...]}.

    `slot` (1..daily_uploads) rotates topic selection so the 2nd and 3rd
    videos of the day never cover the same angle as the 1st.
    """
    mode = cfg["trends"].get("mode", "theme")
    seen = history.recent_topics(cfg["id"])

    if mode == "news":
        queries = cfg["trends"].get("google_news_queries", [])
        headlines: list[str] = []
        for q in queries:
            headlines += news_headlines(q, limit=4)
            if len(headlines) >= 8:
                break
        headlines = [h for h in headlines if h.lower()[:40] not in seen]
        if headlines:
            main = headlines[(slot - 1) % len(headlines)]
            rest = [h for h in headlines if h != main][:3]
            return {"topic": main, "source": "google-news", "headlines": [main] + rest}
        return {"topic": "AI news roundup", "source": "fallback", "headlines": []}

    if mode == "trends":
        geo = cfg["trends"].get("geo", "US")
        trends = [t for t in trending_searches(geo) if t.lower() not in seen]
        if trends:
            pool = trends[:12]
            pick = pool[(slot - 1) % len(pool)]
            return {"topic": pick, "source": "google-trends", "headlines": [pick]}
        return {"topic": None, "source": "fallback", "headlines": []}

    # theme mode (evergreen channels): flavor with trending words when available
    day = datetime.date.today().timetuple().tm_yday
    themes = ["discipline", "consistency", "focus", "resilience", "patience",
              "courage", "purpose", "growth", "gratitude", "momentum"]
    # self-tuning: themes the audience rewarded come first (weekly bias)
    from . import intelligence
    themes = intelligence.theme_priority(cfg["id"], themes)
    theme = themes[(day * 3 + slot - 1) % len(themes)]
    queries = cfg["trends"].get("google_news_queries", [])
    headlines = []
    for q in queries:
        headlines += news_headlines(q, limit=2)
        if headlines:
            break
    return {"topic": f"daily {theme}", "source": "theme", "headlines": headlines[:2]}
