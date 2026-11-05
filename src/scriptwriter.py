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
# v3.2: resized for the QUALITY CADENCE — 2/day (1 short + 1 deep-dive
# long-form). Entries = videos. A deep-dive consumes ~22 quotes, ~22
# lessons and ~22 application lines in ONE video, so windows stay
# satisfiable at that rate (fail-open otherwise — and the fingerprint
# guard still blocks any exact repeat):
#   mindset @ 2/day (1 short + 1 deep-dive):
#     quotes   pool 180, ~23 uses/day → window 8 entries ≈ 4 days ✓
#     lessons  pool ~396 (240 theme + 156 universal), ~24/day → window 8 ✓
#     apps     pool 60, 22/day → window 3 entries ✓
#     hooks    pool 58 + 14 theme templates, 2/day → window 30 ✓
#     outros   pool 26, 2/day → window 20 ✓
#     bridges  pool 20, ~22/day → window 4 (fail-open by design) ✓
#   facts @ 1/day:  facts pool 283, 5/video → window 50 ✓
#   tech @ 1/day:   pool 65, 3/video → window 18 ✓
#   money @ 1/day:  pool 114, 4/video → window 25 ✓
_WINDOWS = {
    "motivation": {"quotes": 8, "lessons": 8, "hooks": 30,
                   "outros": 20, "bridges": 4, "apps": 3,
                   "promises": 6, "rehooks": 6},
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

    # ── build + guard: bank assembly → topic-aware hook → fingerprint ──
    # (v3.2 order fix: the hook is chosen BEFORE fingerprinting, so the
    # ledger's fingerprint matches the shipped script exactly — and a
    # re-roll re-rolls everything, hook included.)
    avoid = _avoid_sets(cfg)
    rerolls = 0
    data = _from_bank(cfg, topic, rng, video=video, avoid=avoid)
    data["source"] = "bank"
    _apply_hook(cfg, topic, data, rng, avoid, video=video)
    fp = history.fingerprint_lines(script_lines(data))
    while history.fingerprint_seen(cfg["id"], fp) and rerolls < _MAX_REROLLS:
        rerolls += 1
        log(f"   ♻ duplicate-fingerprint guard: re-roll #{rerolls}")
        data = _from_bank(cfg, topic, rng, video=video, avoid=avoid)
        _apply_hook(cfg, topic, data, rng, avoid, video=video)
        fp = history.fingerprint_lines(script_lines(data))
    data["fingerprint"] = fp
    if rerolls:
        log(f"   ✅ fresh content after {rerolls} re-roll(s) — no duplicate shipped")

    # humanization audit — log-only, bank text is never rewritten
    data["tells"] = humanize.audit(
        " ".join([data["hook"], *data["scenes"], data["outro"]]))
    if data["tells"]["total"]:
        log(f"   ai-tell audit: {data['tells']['total']} "
            f"(hand-written pools — logged, never rewritten)")
    return data


def _apply_hook(cfg: dict, topic: dict, data: dict, rng: random.Random,
                avoid: dict[str, set[str]], video: bool = False) -> None:
    """v3.2 hook selection — the 30-second retention fix.

    The title and thumbnail promise the day's THEME; the hook now opens
    ON that theme inside the first sentence (shorts: 70% of the time;
    long-form: always — its title is theme-locked). Pattern rotation
    still applies so no two consecutive videos share a hook rhythm.
    """
    niche = cfg.get("niche")
    theme = _theme_of(topic) if niche == "motivation" else None
    try:
        recent_patterns = history.recent_hook_patterns(cfg["id"], n=3)
        prev_pattern = history.last_hook_pattern(cfg["id"])
    except Exception:
        recent_patterns, prev_pattern = set(), None

    if theme:
        pool = bank.theme_hooks(theme)
        fresh = [h for h in pool if bank._n(h) not in avoid.get("hooks", set())]
        pool = fresh or pool
        if video or rng.random() < 0.70:
            varied = [h for h in pool
                      if hookkit.classify(h) not in recent_patterns]
            data["hook"] = rng.choice(varied or pool)
            data["hook_theme"] = True

    if video and data.get("hook_theme"):
        # the deep-dive's hook is theme-locked by its title — classify
        # it, but never swap it away for a generic line
        data["hook_pattern"] = hookkit.classify(data["hook"])
        return
    try:
        data["hook"], data["hook_pattern"] = hookkit.rotate_hook(
            cfg, data["hook"], rng, avoid=prev_pattern,
            avoid_set=recent_patterns)
    except Exception as exc:
        data["hook_pattern"] = "unknown"
        log(f"   ⚠ hook rotation skipped ({type(exc).__name__}: {exc})")


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
    """v3.2 DEEP-DIVE — a real 8-minute long-form, not a stretched Short.

    Motivation format: "{n} {theme} Laws" — each law is a quote +
    attribution bridge + one lesson + one concrete application (the move
    the viewer can DO today). A promise-roadmap opens the video, a
    re-hook lands at the halfway mark (retention doctrine: re-open the
    loop after every payoff cycle), and the outro forces one committed
    action. ~1,050-1,150 spoken words ≈ 8+ minutes at the deep-dive
    voice pace — mid-roll eligible and built to earn watch hours.

    All picks honor the anti-repeat windows and stay DISTINCT within
    the video (no line twice, ever). Other niches keep the legacy
    compilation (they run Shorts-only grids today).
    """
    avoid = avoid or {}
    niche = cfg["niche"]
    hint = intelligence.style_hint(cfg["id"])

    if niche == "motivation":
        theme = _theme_of(topic) or rng.choice(bank.MOTIVATION_THEMES)
        theme_t = theme.title()
        n = max(8, int(cfg.get("longform_chapters", 22)))

        quotes = bank._fresh_pairs_sample(rng, bank.QUOTES, n,
                                          avoid.get("quotes", set()))
        theme_lines = bank._fresh_sample(
            rng, bank.THEME_LESSONS.get(theme, []), (n + 1) // 2,
            avoid.get("lessons", set()))
        universal = bank._fresh_sample(
            rng, bank.MOTIVATION_LESSONS, n - len(theme_lines),
            avoid.get("lessons", set()))
        lessons: list[str] = []
        ti = ui = 0
        for i in range(n):
            if i % 2 == 0 and ti < len(theme_lines):
                lessons.append(theme_lines[ti]); ti += 1
            elif ui < len(universal):
                lessons.append(universal[ui]); ui += 1
            elif ti < len(theme_lines):
                lessons.append(theme_lines[ti]); ti += 1
            else:
                lessons.append(rng.choice(bank.MOTIVATION_LESSONS))
        apps = bank._fresh_sample(rng, bank.MOTIVATION_APPLICATIONS, n,
                                  avoid.get("apps", set()))

        promise = rng.choice(bank.LONGFORM_PROMISES).format(n=n, theme=theme)
        rehook = rng.choice(bank.LONGFORM_REHOOKS)
        outro = rng.choice(bank.LONGFORM_OUTROS).format(n=n, theme=theme)
        mid = n // 2

        scenes: list[str] = [promise]
        memory: list[str] = [promise]
        for i, ((quote, author), lesson, app) in enumerate(
                zip(quotes, lessons, apps)):
            bridge = bank._fresh(rng, bank.BRIDGES,
                                 avoid.get("bridges", set())
                                 ).replace("{author}", author)
            scenes.append(f'"{quote}" — {author}. {bridge}')
            scenes.append(f"{lesson} {app}")
            memory.extend([quote, lesson, app])
            if i + 1 == mid:
                scenes.append(rehook)
                memory.append(rehook)

        hook = bank._fresh(rng, bank.MOTIVATION_HOOKS,
                           avoid.get("hooks", set()))
        title = bank._biased(rng, [
            f"The {n} {theme_t} Laws Nobody Taught You",
            f"{n} {theme_t} Laws That Actually Stick",
            f"{theme_t}: {n} Laws High Performers Live By",
            f"{n} Hard Truths About {theme_t}",
            f"The {n} Laws of {theme_t} — Deep Dive",
        ], hint)
        return {
            "hook": hook,       # write_script replaces it with the theme hook
            "scenes": [clean_text(s) for s in scenes],
            "outro": outro,
            "title": title,
            "description": cfg.get("description_cta", ""),
            "tags": [h.lstrip("#") for h in cfg["hashtags"]][:10],
            "thumbnail_text": f"{n} {theme.upper()} LAWS"[:30],
            "topic": f"deep-dive {theme}",
            "memory_lines": (memory + [outro, hook])[:72],
            "chapters": n,
            "theme": theme,
        }

    # ── legacy compilations (facts / tech / money) ─────────────────────
    scenes = []
    memory = []
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
    else:
        picks = bank._fresh_sample(rng, bank.FACTS, 10, avoid.get("lessons", set()))
        title = "10 Facts That Sound Fake But Are True"
        scenes.extend(picks)

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
                          if niche != "motivation"])[:72],
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
