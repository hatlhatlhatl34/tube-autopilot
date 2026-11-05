"""SEO metadata — auto-title engine + rich description + tag assembly.

Title engine: builds multiple candidates (script title + pattern rewrites),
scores them with CTR heuristics (length sweet-spot, numbers, curiosity
words, question form) plus the weekly self-tuning bias, and ships the best.

Description engine: SEO hook line → engagement question (comment bait,
feeds the algorithm) → optional affiliate links block with disclaimer →
network cross-promo → topic line → hashtags → honest AI-production note.
"""
from __future__ import annotations

import difflib
import re

from . import history, intelligence
from .utils import clamp, clean_text

# CTR power words (curiosity/emotion triggers) used for scoring + rewrites
POWER_WORDS = (
    "nobody", "never", "secret", "truth", "actually", "stop", "warning",
    "mistake", "insane", "crazy", "wild", "instantly", "changes", "real",
    "proven", "rule", "brutal", "unfair", "compounds", "everything",
)

TITLE_PATTERNS = {
    # v3.2 — the death-template killer. "Why {kw} Changes Everything"
    # won the old scoring on EVERY video (11 of 17 titles shipped with
    # one skeleton) and trained the audience to stop reading. Now:
    # ten distinct skeletons per niche + the anti-repeat guard in
    # pick_title() rejects any candidate too similar to the channel's
    # recent titles — one formula can never dominate the feed again.
    "motivation": [
        "The {kw} Rule Nobody Taught You",
        "This Is Why You Keep Failing At {kw}",
        "Read This Before You Give Up On {kw}",
        "{kw}: The Truth Nobody Says Out Loud",
        "5 {kw} Habits That Actually Stick",
        "Nobody Warns You About {kw}",
        "You're Doing {kw} Wrong — Here's The Fix",
        "The 1% Rule Of {kw}",
        "Stop Waiting To Feel Ready ({kw})",
        "{kw} Compounds Faster Than You Think",
    ],
    "facts": [
        "5 Facts About {kw} That Sound Fake",
        "Why {kw} Is Weirder Than You Think",
        "Nobody Warned You About {kw}",
        "The Truth About {kw} Is Wild",
        "How Is {kw} Even Real?",
    ],
    "tech": [
        "Why Everyone Is Talking About {kw}",
        "{kw} Just Changed — Here's What Matters",
        "The {kw} Story You Missed Today",
        "This {kw} Update Is Bigger Than You Think",
    ],
    "money": [
        "Why The Rich Think Differently About {kw}",
        "The {kw} Rule Schools Never Taught You",
        "How {kw} Quietly Builds Wealth",
        "This {kw} Habit Beats Luck Every Time",
    ],
}


def _keywords(text: str, limit: int = 2) -> list[str]:
    # keep hyphenated words whole ("self-belief" ≠ "self")
    words = [w for w in re.split(r"[^a-zA-Z-]+", text or "")
             if 4 <= len(w) <= 14 and w.lower() not in
             {"about", "this", "that", "your", "from", "with", "today",
              "daily", "video", "short", "watch", "here", "what", "they",
              "making", "talking", "says", "said", "being", "have",
              "will", "just", "every", "more", "than", "into", "over",
              # v3.2: format words — never let them become the keyword
              "deep", "dive", "quote", "compilation", "longform", "shorts",
              "unknown", "anonymous"}
             and "-" != w.strip("-")]
    return [w.title() for w in words[:limit]]


def _title_candidates(cfg: dict, script: dict, topic: dict) -> list[str]:
    cands = []
    base = clean_text(script.get("title") or "")
    if base:
        cands.append(base)
    kws = _keywords((topic.get("topic") or "") + " " + (script.get("topic") or base))
    if not kws:
        kws = _keywords(" ".join(script.get("scenes", [])) or cfg["display_name"])
    for kw in kws[:2]:   # v3.2: two keywords → wider candidate spread
        for pat in TITLE_PATTERNS.get(cfg["niche"], TITLE_PATTERNS["facts"]):
            cands.append(pat.format(kw=kw))
    # keep unique, sane lengths
    out, seen = [], set()
    for c in cands:
        c = clean_text(c).strip()
        if 12 <= len(c) <= 70 and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out or ["Today's Drop"]


def score_title(title: str, cfg: dict) -> int:
    """CTR heuristics (v3.2 rebalance).

    The old +2 bonus for titles STARTING with why/how funneled every
    video into one skeleton; curiosity is now carried by power words,
    numbers, questions and second-person pull instead."""
    s = 0
    n = len(title)
    if 40 <= n <= 62:
        s += 3
    elif 30 <= n < 40 or 62 < n <= 72:
        s += 1
    if re.search(r"\d", title):
        s += 2
    if "?" in title:
        s += 2
    low = title.lower()
    power_hits = sum(1 for w in POWER_WORDS if w in low)
    s += min(4, power_hits * 2)
    if low.startswith(("you", "your")):      # second-person pull
        s += 2
    caps = sum(1 for w in title.split() if w.isupper() and len(w) > 3)
    if caps > 2:
        s -= 2
    if n > 78:
        s -= 2
    # weekly bias: the audience's proven favorite style gets a boost
    hint = intelligence.style_hint(cfg["id"])
    if hint and intelligence.classify_title(title) == hint:
        s += 3
    return s


# ── v3.2 title anti-repeat (the monotemplate guard) ───────────────────
_REJECT_SIM = 0.62      # similarity above this vs ANY recent title = reject


def _norm_title(t: str) -> str:
    t = (t or "").lower()
    t = re.sub(r"#\w+", "", t)              # hashtags don't differentiate
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return " ".join(t.split())


def _title_distance(title: str, recent: list[str]) -> float:
    """0..1 similarity vs the MOST similar recent title.

    Blends character-level ratio with token overlap so a keyword swap
    ("Why Patience Changes…" → "Why Courage Changes…") scores as the
    SAME skeleton it is, while a genuinely different formula passes."""
    a = _norm_title(title)
    if not a or not recent:
        return 0.0
    best = 0.0
    for r in recent:
        b = _norm_title(r)
        if not b:
            continue
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        ta, tb = set(a.split()), set(b.split())
        jac = len(ta & tb) / max(1, len(ta | tb))
        best = max(best, max(ratio, 0.6 * ratio + 0.4 * jac))
    return best


def pick_title(cfg: dict, script: dict, topic: dict) -> str:
    cands = _title_candidates(cfg, script, topic)
    try:
        recent = history.recent_titles(cfg["id"], n=12)
    except Exception:
        recent = []
    # v3.2 anti-repeat: a candidate too similar to any of the last 12
    # titles is rejected outright. If everything is rejected (tiny pool
    # edge case) the LEAST similar candidates survive instead.
    fresh = [c for c in cands if not recent
             or _title_distance(c, recent) <= _REJECT_SIM]
    if fresh:
        pool = fresh
    elif recent:
        pool = sorted(cands, key=lambda c: _title_distance(c, recent))[:2]
    else:
        pool = cands
    # v3.2 promise-match: the deep-dive's script title is hand-crafted
    # to match its thumbnail ("24 FOCUS LAWS") — pattern candidates must
    # beat it by a wide margin, not by a tie.
    base = clean_text(script.get("title") or "")
    video = cfg.get("mode") == "video"
    def _score(t):
        s = score_title(t, cfg)
        if video and t == base and s:
            s += 4
        return s
    best = max(pool, key=_score)
    title = clamp(best, 95)
    # #shorts only makes sense on actual Shorts — long-form videos keep clean titles
    if (cfg.get("mode") != "video" and "#shorts" not in title.lower()
            and len(title) <= 86):
        title += " #shorts"
    return title


def _strip_hashtag(h: str) -> str:
    return clean_text(h).lstrip("#").lower()


def _fmt_ts(sec: float) -> str:
    m, s = divmod(max(0, int(sec)), 60)
    return f"{m}:{s:02d}"


_AUTHORS_RE = re.compile(r"—\s*((?:[A-Z][\w.]*\s*)+?)\.(?:\s|$)")
_GENERIC_AUTHORS = {"unknown", "anonymous", "proverb", "traditional"}


def _authors_of(script: dict) -> list[str]:
    """Distinct quote attributions, in spoken order (search surface)."""
    out, seen = [], set()
    for s in script.get("scenes", []):
        for m in _AUTHORS_RE.finditer(s):
            name = " ".join(m.group(1).split())
            if name and name.lower() not in seen and len(name) <= 40 \
                    and name.lower() not in _GENERIC_AUTHORS:
                seen.add(name.lower())
                out.append(name)
    return out


def _chapters_of(script: dict, scene_times) -> list[str]:
    """Timestamp chapters for the deep-dive long-form.

    Segment order is hook(0), promise(1), then quote_i at 2+2i with the
    lesson following — chapter marks ride the QUOTE segments."""
    if not scene_times or not script.get("scenes"):
        return []
    n = int(script.get("chapters") or 0)
    if not n:
        return []
    lines = [f"{_fmt_ts(scene_times[0][0])} The promise"]
    for i in range(n):
        seg = 2 + 2 * i
        if seg < len(scene_times):
            lines.append(f"{_fmt_ts(scene_times[seg][0])} Law {i + 1}")
    last = len(scene_times) - 1
    if last > 2 + 2 * (n - 1):
        lines.append(f"{_fmt_ts(scene_times[last][0])} Your move")
    return lines


def build_description(cfg: dict, script: dict, topic: dict,
                      scene_times=None) -> str:
    desc_lines: list[str] = []

    # 1 — SEO hook line (first 150 chars matter for search + feed preview)
    hook = clean_text(script.get("description") or script.get("hook", ""))
    cta = clean_text(cfg.get("description_cta", ""))
    if hook and hook.lower() == cta.lower():  # bank fallback may reuse the CTA
        hook = ""
    if hook:
        desc_lines.append(clamp(hook, 180))
        desc_lines.append("")

    # 2 — engagement question → comments → algorithm boost
    question = clean_text(cfg.get("engagement_question", ""))
    if question:
        desc_lines.append("💬 " + question)
        desc_lines.append("")

    # 3 — links block (affiliate / tools / anything you add in the yaml)
    links = cfg.get("links") or []
    if links:
        desc_lines.append("LINKS 🔗")
        for ln in links:
            label = clean_text(str(ln.get("label", "")))
            url = clean_text(str(ln.get("url", "")))
            if label and url:
                desc_lines.append(f"• {label}: {url}")
        if cfg.get("affiliate"):
            desc_lines.append("(Some links may be affiliate links — they support "
                              "the channel at no cost to you.)")
        desc_lines.append("")

    # 4 — channel CTA + network cross-promo
    if cta:
        desc_lines.append(cta)
        desc_lines.append("")
    promo = clean_text(cfg.get("cross_promo", ""))
    if promo:
        desc_lines.append(promo)
        desc_lines.append("")

    # 5 — topic line (searchable, honest)
    if topic.get("topic"):
        desc_lines.append(f"Today's topic: {clamp(topic['topic'], 90)}")
        desc_lines.append("")

    # 5b — v3.2 long-form search surface: named authors + timestamps
    if cfg.get("mode") == "video":
        authors = _authors_of(script)
        if authors:
            desc_lines.append("💬 Wisdom in this video: "
                              + ", ".join(authors[:12]) + ".")
            desc_lines.append("")
        chapters = _chapters_of(script, scene_times)
        if chapters:
            desc_lines.append("TIMESTAMPS ⏱")
            desc_lines.extend(chapters)
            desc_lines.append("")

    # 6 — hashtags (first 3 carry the most weight); #shorts only on Shorts
    tags_in = cfg["hashtags"]
    if cfg.get("mode") == "video":
        tags_in = [h for h in tags_in if h.lower() != "#shorts"]
    hashy = " ".join(tags_in[:8])
    desc_lines.append(hashy)

    # 7 — transparent production note (YouTube AI-content best practice)
    desc_lines.append("")
    desc_lines.append("Voice & visuals: AI-assisted production.")

    return "\n".join(desc_lines).lstrip("\n")[:4800]


def build(cfg: dict, script: dict, topic: dict, scene_times=None) -> dict:
    title = pick_title(cfg, script, topic)

    # ---- tags (<= 480 chars total)
    tags: list[str] = []
    for t in script.get("tags", []):
        t = _strip_hashtag(t)
        if t and t not in tags:
            tags.append(t)
    for h in cfg["hashtags"]:
        t = _strip_hashtag(h)
        if t not in tags:
            tags.append(t)
    for w in re.split(r"[^a-z0-9]+", (script.get("title", "")).lower()):
        if len(w) > 3 and w not in tags:
            tags.append(w)
    for w in re.split(r"[^a-z0-9]+", (topic.get("topic") or "").lower()):
        if len(w) > 3 and w not in tags:
            tags.append(w)
    total = 0
    out_tags = []
    for t in tags:
        if total + len(t) + 1 > 470 or len(out_tags) >= 25:
            break
        out_tags.append(t)
        total += len(t) + 1

    return {"title": title, "description": build_description(cfg, script, topic,
                                                          scene_times=scene_times),
            "tags": out_tags, "categoryId": cfg.get("category_id", "22")}
