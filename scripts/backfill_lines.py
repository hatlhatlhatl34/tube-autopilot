#!/usr/bin/env python3
"""One-time v3.1 backfill: give the 6 live Nov-4 videos their `lines` +
`fingerprint` ledger fields (they were recorded before v3.1 existed).

Content source of truth:
  * slots 1, 4, 6 — the exact script.json artifacts from Actions runs
    41927744167 / 41932185262 / 41933393858 (downloaded and verified)
  * slots 2, 3, 5 — ASR transcriptions of the actual uploaded videos,
    mapped back to the exact hand-written bank lines (the banks are
    finite and the transcriptions matched them word-for-word).

After this push, tonight's 19:07 UTC run already excludes every line
the live channel ever spoke — no warm-up gap.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import history  # noqa: E402

VIDEOS = [
    {   # slot 1 — from artifact 13370631586 (run 41927744167)
        "video_id": "8EhLT1VcBE4",
        "hook": "You don't need motivation. You need this.",
        "scenes": [
            "I have not failed. I've just found 10,000 ways that won't work.",
            "Thomas Edison said that for a reason.",
            "One honest hour beats a whole day of distracted effort.",
            "One honest hour beats a whole day of distracted effort.",
            "You don't rise to your goals. You fall to your systems.",
        ],
        "outro": "Follow for your daily dose of discipline.",
    },
    {   # slot 2 — ASR of 1skAAAxSn34, mapped to bank lines
        "video_id": "1skAAAxSn34",
        "hook": "Your future self is watching you right now.",
        "scenes": [
            "Little by little, one travels far.",
            "J.R.R. Tolkien said that for a reason.",
            "You don't rise to your goals. You fall to your systems.",
            "Every rep, every page, every early morning is a vote for who you become.",
            "One honest hour beats a whole day of distracted effort.",
        ],
        "outro": "Save this and reread it tomorrow morning.",
    },
    {   # slot 3 — ASR of 8Upo-cBRT3E, mapped to bank lines
        "video_id": "8Upo-cBRT3E",
        "hook": "Nobody is coming to save you — and that's good news.",
        "scenes": [
            "Success is walking from failure to failure with no loss of enthusiasm.",
            "Winston Churchill said that for a reason.",
            "Nobody claps for the boring years. They clap for results they can't see the roots of.",
            "Small daily wins beat rare heroic efforts every single time.",
            "One honest hour beats a whole day of distracted effort.",
        ],
        "outro": "Save this and reread it tomorrow morning.",
    },
    {   # slot 4 — from artifact 13372661089 (run 41932185262)
        "video_id": "ItQ2rTEfn1I",
        "hook": "The gap between who you are and who you want to be is smaller than you think.",
        "scenes": [
            "You do not rise to the level of your goals. You fall to the level of your systems.",
            "James Clear said that for a reason.",
            "Your habits decide your future long before your goals do.",
            "Progress hides in the boring days you don't feel like showing up.",
            "The person who shows up tired outperforms the person waiting to feel ready.",
        ],
        "outro": "Share this with someone who needs it today.",
    },
    {   # slot 5 (long-form) — ASR of gnlOvKXo3O8, mapped to bank lines
        "video_id": "gnlOvKXo3O8",
        "hook": "You don't need motivation. You need this.",
        "scenes": [
            "Energy and persistence conquer all things. — Benjamin Franklin",
            "Small daily wins beat rare heroic efforts every single time.",
            "The only limit to our realization of tomorrow is our doubts of today. — Franklin D. Roosevelt",
            "You don't need a new plan. You need to finish the one you started.",
            "Do what you feel in your heart to be right — for you'll be criticized anyway. — Eleanor Roosevelt",
            "Discipline is remembering what you want beyond the moment.",
            "You do not rise to the level of your goals. You fall to the level of your systems. — James Clear",
            "You don't need a new plan. You need to finish the one you started.",
        ],
        "outro": "Follow for your daily dose of discipline.",
    },
    {   # slot 6 — from artifact 13372288942 (run 41933393858)
        "video_id": "mvMytEdpWgQ",
        "hook": "Nobody is coming to save you — and that's good news.",
        "scenes": [
            "Success usually comes to those who are too busy to be looking for it.",
            "Henry David Thoreau said that for a reason.",
            "Motivation fades in days. Discipline compounds for decades.",
            "Motivation fades in days. Discipline compounds for decades.",
            "You don't need a new plan. You need to finish the one you started.",
        ],
        "outro": "One percent better every day. Let's go.",
    },
]


def main() -> None:
    entries = history._load("mindset")
    patched = 0
    for v in VIDEOS:
        lines = [v["hook"], *v["scenes"], v["outro"]]
        fp = history.fingerprint_lines(lines)
        hit = False
        for e in entries:
            if e.get("video_id") == v["video_id"]:
                e["lines"] = [history.norm_line(x) for x in lines
                              if history.norm_line(x)][:12]
                e["fingerprint"] = fp
                patched += 1
                hit = True
                print(f"  ✓ {v['video_id']}: {len(e['lines'])} lines, fp {fp}")
                break
        if not hit:
            print(f"  ⚠ {v['video_id']} NOT FOUND in ledger — skipped")

    history._save("mindset", entries)
    print(f"\nbackfilled {patched}/6 entries; ledger now {len(entries)} entries")

    # sanity: every fingerprint distinct?
    fps = [e.get("fingerprint") for e in entries if e.get("fingerprint")]
    assert len(fps) == len(set(fps)), "FINGERPRINT COLLISION IN BACKFILL"
    print(f"sanity: {len(fps)} fingerprints, all distinct ✓")


if __name__ == "__main__":
    main()
