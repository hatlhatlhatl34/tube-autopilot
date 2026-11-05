"""HOOK PATTERNS — the hook-writer doctrine, ported from the
forever-factory (batch-2 skills, 2026-10-27).

The library names nine proven hook patterns. A channel whose hooks
are all one pattern (bold observations, contrarian claims, plain
statements…) trains its audience to stop leaning in. Pattern VARIETY
is retention variety: a question hook after two statements re-opens
the viewer; a negation after an empathy line resets the rhythm.

The doctrine here is adapted to the 4-channel banks WITHOUT rewriting
a single hand-written line:
  * classify(hook) — heuristic labeling of any hook into one of the
    nine patterns (question / negation / statistic / empathy /
    before-after / open-loop / list / contrarian / bold-claim);
  * rotate_hook(cfg, chosen, rng, avoid) — if the bank randomly chose
    a hook in the SAME pattern as the previous video, re-pick within
    the channel's pool preferring a DIFFERENT pattern. Small pools
    may repeat a pattern — rotation degrades gracefully to the bank's
    own choice, never blocks a render.

The pattern label rides into history (hook_pattern) so the
intelligence layer can later learn which PATTERNS earn views, not
just which title styles.
"""
from __future__ import annotations

import random
import re

from . import content_bank as bank

# The nine patterns (hook-writer library):
#   contrarian   challenges what the viewer already believes
#   question     specific, non-obvious, personally addressed
#   statistic    a real, hedged research finding
#   empathy      opens on the viewer's felt pain, not the message
#   before_after the transformation gap, with a timeframe
#   negation     "Stop doing X" / "Stop calling it X"
#   open_loop    names the gap, delays the answer
#   list         promises discrete, countable value
#   bold_claim   a declarative that demands agreement or argument
PATTERNS = ("contrarian", "question", "statistic", "empathy",
            "before_after", "negation", "open_loop", "list", "bold_claim")

_HOOK_POOLS = {
    "motivation": "MOTIVATION_HOOKS",
    "facts": "FACTS_HOOKS",
    "tech": "TECH_HOOKS",
    "money": "MONEY_HOOKS",
}

_STAT_WORDS = re.compile(
    r"\b(stud(y|ies)|research|scientists|survey|percent|%|researchers|"
    r"data|experiment|measured|brain)\b", re.I)
_EMPATHY_WORDS = re.compile(
    r"\b(if you|you've|you feel|you know|your |you are|you're|ever "
    r"notice|we've all)\b", re.I)
_NEGATION = re.compile(r"^(stop|quit|never|don't|do not|nobody|no one)\b", re.I)
_LIST = re.compile(r"\b(three|four|five|six|seven|eight|nine|ten|\d+)\s+"
                   r"(things|tips|ways|facts|rules|signs|reasons|stories|steps)\b", re.I)
_BEFORE_AFTER = re.compile(
    r"\b(before|after|used to|one (day|month|week|year)|six months|"
    r"until|the moment you)\b", re.I)
_OPEN_LOOP = re.compile(
    r"\b(nobody tells you|the reason|one rule|one shift|secret|what "
    r"actually|why you|hidden|quietly)\b", re.I)
_CONTRARIAN = re.compile(
    r"\b(isn'?t|aren'?t|don'?t|doesn'?t|not what|wrong about|no "
    r"longer|instead of|rather than|but)\b", re.I)


def classify(hook: str) -> str:
    """Heuristic pattern label for any hook line (best effort, total
    order: most specific signatures first)."""
    h = (hook or "").strip()
    if not h:
        return "bold_claim"
    if h.rstrip().endswith("?"):
        return "question"
    if _NEGATION.match(h):
        return "negation"
    if _LIST.search(h):
        return "list"
    if _STAT_WORDS.search(h):
        return "statistic"
    if _BEFORE_AFTER.search(h):
        return "before_after"
    if _EMPATHY_WORDS.search(h):
        return "empathy"
    if _OPEN_LOOP.search(h):
        return "open_loop"
    if _CONTRARIAN.search(h):
        return "contrarian"
    return "bold_claim"


def _pool(niche: str) -> list[str]:
    name = _HOOK_POOLS.get(niche)
    return list(getattr(bank, name)) if name else []


def rotate_hook(cfg: dict, chosen: str, rng: random.Random,
                avoid: str | None = None,
                avoid_set: set[str] | None = None) -> tuple[str, str]:
    """Return (hook, pattern). If the bank's random pick repeats a
    recently-used pattern and the pool offers a different one, re-roll
    for pattern variety (still 100% hand-written lines).

    v3.1: `avoid_set` (patterns of the last 3 videos) widens the
    rotation — with 5 videos/day, avoiding only the previous pattern
    let the same rhythm return every 2nd video."""
    niche = cfg.get("niche", "facts")
    pool = _pool(niche)
    pattern = classify(chosen)
    blocked = set(avoid_set or set())
    if avoid:
        blocked.add(avoid)
    if blocked and pattern in blocked and len(pool) > 1:
        others = [h for h in pool if classify(h) not in blocked]
        if not others:                     # tiny pools: at least differ
            others = [h for h in pool if classify(h) != pattern]
        if others:
            pick = others[rng.randrange(len(others))]
            return pick, classify(pick)
    return chosen, pattern
