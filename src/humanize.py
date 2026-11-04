"""The copywriting skill's AI-tells layer, ported from the
forever-factory (batch-3 skills, 2026-11-01).

Doctrine (skills/copywriting/references/ai-tells.md): certain
patterns make copy read machine-written — the "it's not X, it's Y"
contrast reveal, era openers ("in today's world"), recap closers ("in
conclusion"), throat-clearing ("here's the thing"), filler
transitions ("moreover"), rhetorical question-then-answers ("The
result?") and a vocabulary of hollow words (delve, tapestry, unlock,
seamless…). A reader who decides a text was generated starts doubting
its claims — on YouTube that reader is the human AND the recommender,
and the platform's inauthentic-content policy reads the same signals.

Two surfaces, two severities:
  * audit(text) — LOG-ONLY. Our bank text is hand-written and is never
    rewritten by regex; the per-video count rides in script.json and
    the log so any future drift (a bank edit, an imported pool) is
    visible instead of invisible in the prose.
  * scrub(text) — available for any text we DO control at runtime
    (imported pools, future generators): swaps banned vocabulary and
    strips era openers / throat-clearing / filler. Conservative:
    never adds facts, never empties a line, idempotent.

(On the forever-factory this also gated the LLM layer — hard(text)
rejected muse lines that still carried tells after scrub. The LLM is
gone in v3, so hard() is kept for future imported-content gates.)
"""
from __future__ import annotations

import re

# ── the vocabulary layer (swapped in scrub) ─────────────────────────
# (pattern, replacement) — replacements are neutral and never add
# information; they only un-hollow the sentence. Every inflected form
# is listed EXPLICITLY (a backreference would turn "utilize" into
# "usee").
_BANNED_WORDS: list[tuple[str, str]] = [
    (r"\bdelved\b", "dug"), (r"\bdelves\b", "digs"),
    (r"\bdelving\b", "digging"), (r"\bdelve\b", "dig"),
    (r"\btapestries\b", "mixes"), (r"\btapestry\b", "mix"),
    (r"\btestament to\b", "proof of"),
    (r"\brealms\b", "areas"), (r"\brealm\b", "area"),
    (r"\bembarks\b", "starts"), (r"\bembarked\b", "started"),
    (r"\bembarking\b", "starting"), (r"\bembark\b", "start"),
    (r"\bbeacons\b", "signals"), (r"\bbeacon\b", "signal"),
    (r"\bmultifaceted\b", "many-sided"),
    (r"\bparadigms\b", "models"), (r"\bparadigm\b", "model"),
    (r"\bsynergies\b", "overlaps"), (r"\bsynergy\b", "overlap"),
    (r"\bsynergistic\b", "overlapping"),
    (r"\ba myriad of\b", "many"), (r"\bmyriad\b", "many"),
    (r"\ba plethora\b", "plenty"), (r"\bplethora of\b", "plenty of"),
    (r"\bmeticulously\b", "carefully"), (r"\bmeticulous\b", "careful"),
    (r"\butilizes\b", "uses"), (r"\butilized\b", "used"),
    (r"\butilizing\b", "using"), (r"\butilize\b", "use"),
    (r"\bleverages\b", "uses"), (r"\bleveraged\b", "used"),
    (r"\bleveraging\b", "using"), (r"\bleverage\b", "use"),
    (r"\bsupercharges\b", "boosts"), (r"\bsupercharged\b", "boosted"),
    (r"\bsupercharging\b", "boosting"), (r"\bsupercharge\b", "boost"),
    (r"\bturbocharges\b", "boosts"), (r"\bturbocharged\b", "boosted"),
    (r"\bturbocharging\b", "boosting"), (r"\bturbocharge\b", "boost"),
    (r"\bgame-changer\b", "big shift"), (r"\bgame-changing\b", "shifting"),
    (r"\bcutting-edge\b", "new"),
    (r"\bseamlessly\b", "smoothly"), (r"\bseamless\b", "smooth"),
    (r"\beffortlessly\b", "easily"), (r"\beffortless\b", "easy"),
    (r"\bunlocked\b", "opened"), (r"\bunlocking\b", "opening"),
    (r"\bunlocks\b", "opens"), (r"\bunlock\b", "open"),
    (r"\bunleashes\b", "frees"), (r"\bunleashed\b", "freed"),
    (r"\bunleashing\b", "freeing"), (r"\bunleash\b", "free"),
    (r"\belevates\b", "lifts"), (r"\belevate\b", "lift"),
    (r"\belevated\b", "lifted"), (r"\belevating\b", "lifting"),
    (r"\bholistic\b", "whole-picture"),
    (r"\btransformative\b", "deep"),
    (r"\bworld-class\b", "great"), (r"\bbest-in-class\b", "great"),
    (r"\bnext-level\b", "new"),
    (r"\bever-evolving\b", "changing"),
    (r"\bharnesses\b", "uses"), (r"\bharnessed\b", "used"),
    (r"\bharnessing\b", "using"), (r"\bharness\b", "use"),
    (r"\bnavigates\b", "handles"), (r"\bnavigate\b", "handle"),
    (r"\bnavigated\b", "handled"), (r"\bnavigating\b", "handling"),
    (r"\bplays a crucial role\b", "matters"),
    (r"\bsay goodbye to\b", "let go of"),
    (r"\breimagined\b", "rebuilt"), (r"\breimagining\b", "rebuilding"),
]

# leading-clause strips: applied at the start of any SENTENCE, and
# only when what remains still carries the sentence (>= 4 words).
_LEADING_CLAUSES: list[str] = [
    r"in today'?s (?:fast-paced )?world[,:]?\s+",
    r"in this day and age[,:]?\s+",
    r"when it comes to [^,.;:]{1,40},\s+",
    r"it'?s worth noting(?: that)?[,:]?\s+",
    r"worth noting that\s+",
    r"(?:moreover|additionally|furthermore|importantly)[,:]?\s+",
    r"in conclusion[,:]?\s+",
    r"ultimately[,:]?\s+",
    r"at the end of the day[,:]?\s+",
    r"let me be clear[,:]?\s+",
    r"here'?s the thing[,:]?\s+",
    r"here'?s what nobody tells you[,:]?\s+",
    r"let'?s dive in\b",
]

# ── the audit layer (counted everywhere, enforced nowhere) ─────────
_AUDIT_PATTERNS: dict[str, str] = {
    "contrast_reveal": r"(?:\b(?:it|this|that|the question)?'?s? not [^.!?\n]{2,60}"
                       r"(?:-+|,|;|\.|\bnut\b)?\s*(?:it'?s|it is|but|the real)\b"
                       r"|\bnot just\b"
                       r"|\bless [a-z]+,? more [a-z]+\b)",
    "era_opener": r"\bin today'?s (?:world|fast-paced world|day and age)\b",
    "throat_clear": r"\b(?:here'?s the thing|let me be clear|"
                    r"here'?s what nobody tells you)\b",
    "recap_closer": r"(?:^|(?<=[.!?]\s))(?:in conclusion|ultimately|"
                    r"at the end of the day)\b",
    "filler": r"\b(?:moreover|additionally|furthermore|importantly|"
             r"it'?s worth noting)\b",
    "rhetorical_q": r"\b(?:the (?:result|catch|point|problem|takeaway)\?|"
                    r"why does this matter\?|the answer\?)",
    "colon_reveal": r"\b(?:one word:|the best part:|here'?s the secret:|"
                    r"the truth:)",
    "banned_vocab": r"\b(?:delv(?:e|es|ed|ing)|tapestr(?:y|ies)|testament|"
                    r"realms?|embarks?|beacons?|multifaceted|paradigms?|"
                    r"synerg(?:y|ies)|myriad|plethora|meticulous(?:ly)?|"
                    r"utiliz\w+|leverag\w+|supercharg\w+|turbocharg\w+|"
                    r"game-chang\w+|cutting-edge|seamless\w*|"
                    r"effortless\w*|unlock\w*|unleash\w*|elevat\w+|"
                    r"holistic|transformative|world-class|best-in-class|"
                    r"next-level|ever-evolving|harness\w*)\b",
    "intensifier": r"\b(?:truly|genuinely|incredibly|deeply|fundamentally|"
                   r"literally|utterly|profoundly)\b",
}

# hard tells: a line still carrying one of these AFTER scrub would be
# rejected by an imported-content gate (kept for future use).
_HARD_CATEGORIES = ("era_opener", "throat_clear", "recap_closer",
                    "filler", "rhetorical_q", "colon_reveal",
                    "banned_vocab")

_COMPILED_LEAD = [re.compile(p, re.IGNORECASE) for p in _LEADING_CLAUSES]
_COMPILED_AUDIT = {k: re.compile(p, re.IGNORECASE)
                   for k, p in _AUDIT_PATTERNS.items()}
_COMPILED_WORDS = [(re.compile(p, re.IGNORECASE), r) for p, r in _BANNED_WORDS]


def _strip_leading(sentence: str) -> str:
    """Remove an AI-tell leading clause from ONE sentence, but only
    if what remains is still a sentence (>= 4 words)."""
    for rx in _COMPILED_LEAD:
        m = rx.match(sentence)
        if not m:
            continue
        rest = sentence[m.end():]
        if len(rest.split()) >= 4:
            rest = rest[0].upper() + rest[1:] if rest else rest
            return rest
    return sentence


def scrub(text: str) -> str:
    """Deterministic fixups for runtime-controlled text only (never the
    hand-written banks). Conservative by design: swaps banned
    vocabulary for neutral words, strips era openers / throat-clearing
    / filler / recap closers from sentence starts. Never adds facts,
    never empties a line, idempotent."""
    if not text:
        return text
    for rx, repl in _COMPILED_WORDS:
        text = rx.sub(repl, text)
    parts = re.split(r"(?<=[.!?]) +", text)
    cleaned = [_strip_leading(p) for p in parts]
    out = " ".join(cleaned).strip()
    out = re.sub(r"\s+", " ", out)
    return out or text


def audit(text: str) -> dict[str, int]:
    """Count AI tells by category. LOG-ONLY: hand pools keep their
    deliberate, sparse devices; the count exposes drift."""
    report = {k: len(rx.findall(text))
              for k, rx in _COMPILED_AUDIT.items()}
    report["total"] = sum(v for k, v in report.items() if k != "total")
    return report


def hard(text: str) -> list[str]:
    """Hard tells that survived a scrub — an imported-content gate
    would reject the line. Contrast reveals and intensifier stacks
    are NOT here: audited, not banned."""
    return [k for k in _HARD_CATEGORIES
            if _COMPILED_AUDIT[k].search(text)]
