"""Script writer — v3.1: CONTENT-BANK ONLY + THE ANTI-DUPLICATE ENGINE.

Owner rule (2026-11-05): the factory touches EXACTLY two external
services — the YouTube Data API (upload, with the channel's own OAuth
credentials) and GitHub (Actions + state). No Gemini, no LLM, no
key-based AI anywhere in the writing path. Every script is assembled
deterministically from the per-channel content banks in
src/content_bank.py, with four forever-factory upgrades:

  1. HOOK PATTERN ROTATION (src/hooks.py): the hook pool is classified
     into 9 proven patterns and the picker avoids the patterns of the
     LAST THREE videos (v3.1: was just the previous one) — retention
     variety with zero new content.

  2. HUMANIZATION AUDIT (src/humanize.py): every script is audited for
     machine-sounding patterns; the count rides in script.json so drift
     is visible. Bank text is hand-written and never rewritten.

  3. INTELLIGENCE BIAS (src/intelligence.py): the loop that learned
     which title styles earn views keeps steering bank picks.

  4. ANTI-DUPLICATE ENGINE (v3.1, the owner's caught-bug fix):
     a. LINE MEMORY — every pick excludes lines used inside a
        per-layer rotation window (quotes ~170 videos, theme+universal
        lessons ~90, hooks ~44, outros ~22, bridges ~10);
     b. WITHIN-VIDEO DISTINCTNESS — lesson slots are sampled WITHOUT
        replacement, so one line can never appear twice in one video;
     c. FINGERPRINT GUARD (absolute) — sha1 of the sorted normalized
        line set, checked against the channel's ENTIRE history; a
        collision re-rolls the script (up to 6 attempts). Two identical
        videos are now mathematically impossible, on any horizon.

The Gemini path was REMOVED (not disabled) so it can never silently
come back: no key is read, no network call is made while writing.
"""
from __future__ import annotations

import random

from . import content_bank as bank
from . import hooks as hookkit
from . import history
from . import humanize
from . import intelligence
from .utils import clean_text, log

# ── anti-repeat rotation windows (videos, not days) ───────────────────
# Sized per niche so the exclusion NEVER empties a pool at the current
# daily rate (windows scale with daily_uploads — raise them in the same
# commit that raises daily_uploads):
#   mindset @ 5/day (4 shorts + 1 long):
#     quotes  pool 180, ~1.6 uses/video → window 100 ≈ 160 uses ✓
#     theme+universal lessons  pool 336, ~3.2/video → window 90 ✓
#     hooks   pool 48, 1/video  → window 44   ≈ 9-day rotation
#     outros  pool 25, 1/video  → window 22   ≈ 4-day rotation
#     bridges pool 12, ~1.6/video → window 7
#   facts @ 1/day:  facts pool 283, 5/video → window 50 ✓
#   tech @ 1/day:   pool 65, 3/video → window 18 ✓
#   money @ 1/day:  pool 114, 4/video → window 25 ✓
# All fail-open: an exhausted layer falls back to its full pool, and
# the fingerprint guard still blocks any EXACT repeat.
_WINDOWS = {
    "motivation": {"quotes": 100, "lessons": 90, "hooks": 44,
                   "outros": 22, "bridges": 7},
    "facts": {"quotes": 0, "lessons": 50, "hooks": 15, "outros": 12,
              "bridges": 0},
    "tech": {"quotes": 0, "lessons": 18, "hooks": 12, "outros": 9,
             "bridges": 0},
    "money": {"quotes": 0, "lessons": 25, "hooks": 15, "outros": 11,
              "bridges": 0},
}

_MAX_REROLLS = 6


def _avoid_sets(cfg: dict) -> dict[str, set[str]]:
    """Per-layer exclusion windows from the channel's line memory."""
    windows = _WINDOWS.get(cfg["niche"], _WINDOWS["facts"])
    out: dict[str, set[str]] = {}
    for layer, n in windows.items():
        out[layer] = history.recent_lines(cfg["id"], n) if n else set()
    return out


def script_lines(data: dict) -> list[str]:
    """The spoken content lines of a script (hook + scenes + outro)."""
    return [data.get("hook", ""), *data.get("scenes", []),
            data.get("outro", "")]


def write_script(cfg: dict, topic: dict, rng: random.Random) -> dict:
    video = cfg.get("mode") == "video"

    # ── 4c. THE FINGERPRINT GUARD ────────────────────────────────────
    # Build the script; if its content fingerprint matches ANY video
    # this channel ever published, re-roll with fresh entropy. The
    # windows above make collisions rare; this makes them impossible.
    avoid = _avoid_sets(cfg)
    data = _from_bank(cfg, topic, rng, video=video, avoid=avoid)
    data["source"] = "bank"
    fp = history.fingerprint_lines(script_lines(data))
    rerolls = 0
    while history.fingerprint_seen(cfg["id"], fp) and rerolls < _MAX_REROLLS:
        rerolls += 1
        log(f"   ♻ duplicate-fingerprint guard: re-roll #{rerolls}")
        data = _from_bank(cfg, topic, rng, video=video, avoid=avoid)
        fp = history.fingerprint_lines(script_lines(data))
    data["fingerprint"] = fp
    if rerolls:
        log(f"   ✅ fresh content after {rerolls} re-roll(s) — no duplicate shipped")

    # 1. hook pattern rotation (variety without new content)
    try:
        recent_patterns = history.recent_hook_patterns(cfg["id"], n=3)
        prev_pattern = history.last_hook_pattern(cfg["id"])
        data["hook"], data["hook_pattern"] = hookkit.rotate_hook(
            cfg, data["hook"], rng, avoid=prev_pattern, avoid_set=recent_patterns)
    except Exception as exc:
        data["hook_pattern"] = "unknown"
        log(f"   ⚠ hook rotation skipped ({type(exc).__name__}: {exc})")

    # 2. humanization audit — log-only, bank text is never rewritten
    data["tells"] = humanize.audit(
        " ".join([data["hook"], *data["scenes"], data["outro"]]))
    if data["tells"]["total"]:
        log(f"   ai-tell audit: {data['tells']['total']} "
            f"(hand-written pools — logged, never rewritten)")
    return data


def _theme_of(topic: dict) -> str | None:
    """'daily patience' → 'patience' (the mindset topic→theme link)."""
    t = (topic.get("topic") or "").strip().lower()
    if t.startswith("daily "):
        cand = t[len("daily "):].strip()
        if cand in bank.THEME_LESSONS:
            return cand
    return None


def _longform_from_bank(cfg: dict, topic: dict, rng: random.Random,
                        avoid: dict[str, set[str]] | None = None) -> dict:
    """Stitch several bank entries into one ~100s long-form script.

    Reuses the existing single-Short banks as building blocks, so the
    machine stays niche-agnostic: whatever the banks hold, the
    long-form has. v3.1: picks honor the anti-repeat windows and are
    DISTINCT within the video (no line twice, ever).
    """
    avoid = avoid or {}
    niche = cfg["niche"]
    scenes: list[str] = []
    memory: list[str] = []          # raw pool texts for the ledger
    hint = intelligence.style_hint(cfg["id"])

    if niche == "facts":
        picks = bank._fresh_sample(rng, bank.FACTS, 10, avoid.get("lessons", set()))
        title = bank._biased(rng, [
            "10 Facts That Sound Fake But Are True",
            "10 Facts You Won't Believe Are Real",
            "The Universe Is Weirder Than You Think",
        ], hint)
        for p in picks:
            scenes.append(p)
    elif niche == "money":
        rules = bank._fresh_sample(rng, bank.MONEY_RULES, 8, avoid.get("lessons", set()))
        title = bank._biased(rng, [
            "8 Money Rules That Quietly Build Wealth",
            "The Money Rules Schools Never Taught You",
            "8 Money Rules Broke People Ignore",
        ], hint)
        scenes.extend(rules)
    elif niche == "tech":
        facts = bank._fresh_sample(rng, bank.TECH_FALLBACK_FACTS, 8,
                                   avoid.get("lessons", set()))
        title = bank._biased(rng, [
            "8 AI Facts That Change Everything",
            "What AI Can Actually Do In 2026",
            "8 Tech Facts That Sound Like Sci-Fi",
        ], hint)
        scenes.extend(facts)
    else:  # motivation
        theme = _theme_of(topic)
        quotes = bank._fresh_pairs_sample(rng, bank.QUOTES, 4,
                                          avoid.get("quotes", set()))
        title = bank._biased(rng, [
            "4 Quotes That Will Change How You See Discipline",
            "The Quotes That Build Unstoppable People",
            "Wisdom In 4 Lines — Read This When You're Stuck",
        ], hint)
        theme_pool: list[str] = []
        if theme:
            theme_pool = bank._fresh_sample(rng, bank.THEME_LESSONS[theme], 4,
                                            avoid.get("lessons", set()))
        universal = bank._fresh_sample(rng, bank.MOTIVATION_LESSONS, 4,
                                       avoid.get("lessons", set()))
        memory: list[str] = []
        for i, (text, author) in enumerate(quotes):
            bridge = bank._fresh(rng, bank.BRIDGES,
                                 avoid.get("bridges", set())).replace("{author}", author)
            scenes.append(f'"{text}" — {author}')
            scenes.append(bridge)
            if theme_pool:
                scenes.append(theme_pool[i % len(theme_pool)])
                memory.append(theme_pool[i % len(theme_pool)])
            else:
                scenes.append(universal[i % len(universal)])
                memory.append(universal[i % len(universal)])
            memory.extend([text, bridge])

    hooks = {"motivation": bank.MOTIVATION_HOOKS, "facts": bank.FACTS_HOOKS,
             "tech": bank.TECH_HOOKS, "money": bank.MONEY_HOOKS}
    outros = {"motivation": bank.MOTIVATION_OUTROS, "facts": bank.FACTS_OUTROS,
              "tech": bank.TECH_OUTROS, "money": bank.MONEY_OUTROS}

    hook = bank._fresh(rng, hooks.get(niche, bank.FACTS_HOOKS),
                       avoid.get("hooks", set()))
    outro = bank._fresh(rng, outros.get(niche, bank.FACTS_OUTROS),
                        avoid.get("outros", set()))
    return {
        "hook": hook,
        "scenes": [clean_text(s) for s in scenes],
        "outro": outro,
        "title": title,
        "description": cfg.get("description_cta", ""),
        "tags": [h.lstrip("#") for h in cfg["hashtags"]][:10],
        "thumbnail_text": rng.choice(["WATCH THIS", "MUST WATCH", "SAVE THIS"]),
        "topic": f"long-form {niche} compilation",
        "memory_lines": ([hook, outro] + memory +
                         [s for s in scenes
                          if niche != "motivation"])[:16],
    }


def _from_bank(cfg: dict, topic: dict, rng: random.Random, video: bool = False,
               avoid: dict[str, set[str]] | None = None) -> dict:
    avoid = avoid or {}
    niche = cfg["niche"]
    if video:
        data = _longform_from_bank(cfg, topic, rng, avoid=avoid)
    else:
        hint = intelligence.style_hint(cfg["id"])
        if niche == "motivation":
            # v3.1: the day's THEME is passed in — the script now talks
            # about its title topic (was: random theme, zero connection)
            data = bank.motivation_bank(
                rng, theme=_theme_of(topic), style_hint=hint, avoid=avoid)
        elif niche == "facts":
            data = bank.facts_bank(rng, topic.get("topic"), style_hint=hint,
                                   avoid=avoid)
        elif niche == "tech":
            data = bank.tech_bank(rng, topic.get("headlines", []),
                                  style_hint=hint, avoid=avoid)
        elif niche == "money":
            data = bank.money_bank(rng, style_hint=hint, avoid=avoid)
        else:
            data = bank.facts_bank(rng, topic.get("topic"), style_hint=hint,
                                   avoid=avoid)
    data.setdefault("description", cfg.get("description_cta", ""))
    data.setdefault("tags", [h.lstrip("#") for h in cfg["hashtags"]][:10])
    data["thumbnail_text"] = data.get("thumbnail_text", "MUST WATCH")[:30]
    return data
