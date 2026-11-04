"""Script writer — v3: CONTENT-BANK ONLY (the no-API doctrine).

Owner rule (2026-11-05): the factory touches EXACTLY two external
services — the YouTube Data API (upload, with the channel's own OAuth
credentials) and GitHub (Actions + state). No Gemini, no LLM, no
key-based AI anywhere in the writing path. Every script is assembled
deterministically from the per-channel content banks in
src/content_bank.py (mindset 49 quotes + 16 lessons, facts 59, tech 23
+ live headlines, money 38), with three forever-factory upgrades:

  1. HOOK PATTERN ROTATION (src/hooks.py, from the hook-writer
     doctrine): the hook pool is classified into 9 proven patterns
     (contrarian / question / statistic / empathy / before-after /
     negation / open-loop / list / bold-claim) and the picker avoids
     repeating the previous video's pattern — retention variety with
     zero new content.

  2. HUMANIZATION AUDIT (src/humanize.py, from the ai-tells skill):
     every script is audited for machine-sounding patterns (era
     openers, filler transitions, hollow vocabulary); the count rides
     in script.json so drift is visible. Bank text is hand-written and
     is never rewritten by regex — audit-only, per the doctrine.

  3. INTELLIGENCE BIAS (src/intelligence.py): the loop that learned
     which title styles earn views keeps steering bank picks.

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


def write_script(cfg: dict, topic: dict, rng: random.Random) -> dict:
    video = cfg.get("mode") == "video"
    data = _from_bank(cfg, topic, rng, video=video)
    data["source"] = "bank"

    # 1. hook pattern rotation (variety without new content)
    try:
        prev_pattern = history.last_hook_pattern(cfg["id"])
        data["hook"], data["hook_pattern"] = hookkit.rotate_hook(
            cfg, data["hook"], rng, avoid=prev_pattern)
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


def _longform_from_bank(cfg: dict, topic: dict, rng: random.Random) -> dict:
    """Stitch several bank entries into one ~100s long-form script.

    Reuses the existing single-Short banks as building blocks, so the
    machine stays niche-agnostic: whatever the banks hold, the
    long-form has.
    """
    niche = cfg["niche"]
    scenes: list[str] = []

    if niche == "facts":
        picks = rng.sample(bank.FACTS, 10)
        title = bank._biased(rng, [
            "10 Facts That Sound Fake But Are True",
            "10 Facts You Won't Believe Are Real",
            "The Universe Is Weirder Than You Think",
        ])
        for p in picks:
            fact, why = p[0], p[1]
            scenes.append(fact)
            scenes.append(why)
    elif niche == "money":
        rules = rng.sample(bank.MONEY_RULES, 8)
        title = bank._biased(rng, [
            "8 Money Rules That Quietly Build Wealth",
            "The Money Rules Schools Never Taught You",
            "8 Money Rules Broke People Ignore",
        ])
        for r in rules:
            rule, detail = r[0], r[1]
            scenes.append(rule)
            scenes.append(detail)
    elif niche == "tech":
        facts = rng.sample(bank.TECH_FALLBACK_FACTS, 8)
        title = bank._biased(rng, [
            "8 AI Facts That Change Everything",
            "What AI Can Actually Do In 2026",
            "8 Tech Facts That Sound Like Sci-Fi",
        ])
        for f in facts:
            fact, why = f[0], f[1]
            scenes.append(fact)
            scenes.append(why)
    else:  # motivation
        quotes = rng.sample(bank.QUOTES, 4)
        title = bank._biased(rng, [
            "4 Quotes That Will Change How You See Discipline",
            "The Quotes That Build Unstoppable People",
            "Wisdom In 4 Lines — Read This When You're Stuck",
        ])
        for q in quotes:
            text, author, lesson = q
            scenes.append(f'"{text}" — {author}')
            scenes.append(rng.choice(bank.MOTIVATION_LESSONS))

    hooks = {"motivation": bank.MOTIVATION_HOOKS, "facts": bank.FACTS_HOOKS,
             "tech": bank.TECH_HOOKS, "money": bank.MONEY_HOOKS}
    outros = {"motivation": bank.MOTIVATION_OUTROS, "facts": bank.FACTS_OUTROS,
              "tech": bank.TECH_OUTROS, "money": bank.MONEY_OUTROS}

    return {
        "hook": rng.choice(hooks.get(niche, bank.FACTS_HOOKS)),
        "scenes": [clean_text(s) for s in scenes],
        "outro": rng.choice(outros.get(niche, bank.FACTS_OUTROS)),
        "title": title,
        "description": cfg.get("description_cta", ""),
        "tags": [h.lstrip("#") for h in cfg["hashtags"]][:10],
        "thumbnail_text": rng.choice(["WATCH THIS", "MUST WATCH", "SAVE THIS"]),
        "topic": f"long-form {niche} compilation",
    }


def _from_bank(cfg: dict, topic: dict, rng: random.Random, video: bool = False) -> dict:
    if video:
        data = _longform_from_bank(cfg, topic, rng)
    else:
        niche = cfg["niche"]
        hint = intelligence.style_hint(cfg["id"])
        if niche == "motivation":
            data = bank.motivation_bank(rng, style_hint=hint)
        elif niche == "facts":
            data = bank.facts_bank(rng, topic.get("topic"), style_hint=hint)
        elif niche == "tech":
            data = bank.tech_bank(rng, topic.get("headlines", []), style_hint=hint)
        elif niche == "money":
            data = bank.money_bank(rng, style_hint=hint)
        else:
            data = bank.facts_bank(rng, topic.get("topic"), style_hint=hint)
    data.setdefault("description", cfg.get("description_cta", ""))
    data.setdefault("tags", [h.lstrip("#") for h in cfg["hashtags"]][:10])
    data["thumbnail_text"] = data.get("thumbnail_text", "MUST WATCH")[:30]
    return data
