"""Self-tuning intelligence — the factory's performance memory.

Every Monday the weekly job joins each channel's upload history with live
YouTube statistics, learns what actually earned views, and writes
data/history/bias.json.  The daily generators (Gemini prompt, bank titles,
theme selection) read those biases — so the factory tunes itself week after
week with ZERO code changes, forever.

bias.json schema (per channel):
{
  "updated": "2026-09-14",
  "samples": 12,                       # videos measured so far
  "title_style": "question",           # best-performing title style
  "title_style_scores": {"question": 812, "number": 240},
  "hot_topics": ["discipline", "focus"],
  "note": "human-readable one-liner shown in the weekly report"
}
"""
from __future__ import annotations

import datetime
import json
import re

from .config import HISTORY_DIR
from .utils import log

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "your", "you", "this", "that", "is", "are", "be", "it", "its", "how",
    "why", "what", "when", "who", "at", "from", "by", "as", "daily", "new",
    "today", "update", "news", "best", "top", "vs", "about",
}

_STYLES = (
    ("question", lambda t: "?" in t),
    ("number", lambda t: bool(re.search(r"\d", t))),
    ("why", lambda t: t.lower().startswith("why")),
    ("how", lambda t: t.lower().startswith("how")),
    ("you", lambda t: " you" in " " + t.lower() or "your" in t.lower()),
    ("this", lambda t: t.lower().startswith(("this", "these"))),
)


def classify_title(title: str) -> str:
    for name, test in _STYLES:
        try:
            if test(title):
                return name
        except Exception:
            continue
    return "plain"


def _bias_path():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR / "bias.json"


def load_bias() -> dict:
    try:
        return json.loads(_bias_path().read_text())
    except Exception:
        return {}


def _history_map(channel_id: str) -> dict:
    """video_id -> history entry (topic)."""
    from . import history
    out = {}
    for e in history._load(channel_id):
        if e.get("video_id"):
            out[e["video_id"]] = e
    return out


def _keywords(text: str, limit: int = 6) -> list[str]:
    words = [w for w in re.split(r"[^a-z0-9']+", (text or "").lower())
             if len(w) > 3 and w not in STOPWORDS]
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:limit]


def recompute(channel_id: str, recent_rows: list[dict]) -> dict | None:
    """recent_rows: [{video_id,title,views,...}] from youtube.channel_stats().

    Learns title-style performance + hot topic keywords, updates bias.json.
    Returns the new bias entry (or None while warming up).
    """
    hmap = _history_map(channel_id)
    joined = []
    for row in recent_rows:
        vid = row.get("video_id")
        if vid and vid in hmap:
            joined.append((row, hmap[vid]))

    if len(joined) < 3:
        log(f"   🧠 {channel_id}: only {len(joined)} measured videos — warming up, no bias yet")
        return None

    # ---- title style scores (average views per style)
    style_views: dict[str, list[int]] = {}
    for row, _ in joined:
        st = classify_title(row.get("title", ""))
        style_views.setdefault(st, []).append(max(1, row.get("views", 0)))
    scores = {k: int(sum(v) / len(v)) for k, v in style_views.items() if v}
    best_style = max(scores, key=scores.get) if scores else None

    # ---- hot topics from the top 30% of videos by views
    ranked = sorted(joined, key=lambda p: p[0].get("views", 0), reverse=True)
    top_slice = ranked[: max(1, len(ranked) // 3)]
    hot: dict[str, int] = {}
    for row, entry in top_slice:
        for kw in _keywords(entry.get("topic", "")) + _keywords(row.get("title", "")):
            hot[kw] = hot.get(kw, 0) + 1
    hot_topics = [k for k, _ in sorted(hot.items(), key=lambda p: -p[1])][:8]

    note = (f"{len(joined)} videos measured — '{best_style}' titles perform best "
            f"(avg {scores.get(best_style, 0):,} views); lean into: "
            f"{', '.join(hot_topics[:5]) or 'no clear topic signal yet'}")

    bias = load_bias()
    bias[channel_id] = {
        "updated": datetime.date.today().isoformat(),
        "samples": len(joined),
        "title_style": best_style,
        "title_style_scores": scores,
        "hot_topics": hot_topics,
        "note": note,
    }
    _bias_path().write_text(json.dumps(bias, indent=1, ensure_ascii=False))
    log(f"   🧠 {channel_id}: bias updated → style='{best_style}', hot topics: {hot_topics[:4]}")
    return bias[channel_id]


def hints_for(cfg: dict) -> str:
    """Compact performance-memory line injected into the Gemini prompt."""
    b = load_bias().get(cfg["id"])
    if not b or b.get("samples", 0) < 3:
        return ""
    parts = []
    if b.get("title_style"):
        parts.append(f"titles styled as '{b['title_style']}' earned the most views")
    if b.get("hot_topics"):
        parts.append("audience responds to: " + ", ".join(b["hot_topics"][:5]))
    return "; ".join(parts)


def style_hint(channel_id: str) -> str | None:
    b = load_bias().get(channel_id)
    if b and b.get("samples", 0) >= 3 and b.get("title_style"):
        return b["title_style"]
    return None


def reorder_for_style(candidates: list[str], style: str | None) -> list[str]:
    """Bias a list of bank titles toward the winning style (stable order)."""
    if not style:
        return list(candidates)
    preferred = [t for t in candidates if classify_title(t) == style]
    rest = [t for t in candidates if classify_title(t) != style]
    return preferred + rest


def theme_priority(channel_id: str, themes: list[str]) -> list[str]:
    """Reorder evergreen themes so ones matching hot topics come first."""
    b = load_bias().get(channel_id) or {}
    hot = set(b.get("hot_topics", []))
    if not hot:
        return list(themes)
    scored = sorted(themes, key=lambda t: -len(hot & set(t.lower().split())))
    return scored
