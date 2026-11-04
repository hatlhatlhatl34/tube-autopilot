#!/usr/bin/env python3
"""Weekly intelligence — analytics report + self-tuning brain update.

Runs every Monday via .github/workflows/weekly-report.yml:
  1. Pulls live stats for all 4 channels (YouTube Data API).
  2. Feeds them to src/intelligence.py → learns what earned views,
     rewrites data/history/bias.json (committed back to the repo).
  3. Opens a "Weekly Empire Report" issue (you get it by email).

From Monday onward, every daily video is generated biased toward what the
audience actually rewarded — no code changes, ever.
"""
from __future__ import annotations

import sys

from src.config import CHANNEL_IDS, load_channel
from src.utils import is_ci, log


def _fmt(n: int) -> str:
    return f"{n:,}"


def build_markdown() -> str:
    from src import intelligence, youtube

    lines = ["# 📊 Weekly Empire Report", "",
             "| Channel | Subs | Total views | Videos | Recent avg views |",
             "|---|---|---|---|---|"]
    details = []
    learned = []
    for cid in CHANNEL_IDS:
        cfg = load_channel(cid)
        try:
            st = youtube.channel_stats(cfg)
        except Exception as e:
            lines.append(f"| {cfg['display_name']} | ⚠️ {type(e).__name__} | - | - | - |")
            continue
        avg = sum(r["views"] for r in st["recent"]) / max(1, len(st["recent"]))
        lines.append(f"| {st['name']} | {_fmt(st['subscribers'])} | "
                     f"{_fmt(st['views'])} | {_fmt(st['videos'])} | {int(avg):,} |")
        details.append((st, cfg))

        # ---- self-tuning: learn from this channel's performance
        try:
            bias = intelligence.recompute(cid, st["recent"])
            if bias:
                learned.append((cfg["display_name"], bias["note"]))
        except Exception as e:
            log(f"   ⚠ intelligence.recompute({cid}) failed: {e}")

    for st, cfg in details:
        lines += [f"\n## {st['name']}", ""]
        if st["recent"]:
            lines += ["| Video | Views | Likes | Comments |", "|---|---|---|---|"]
            for r in st["recent"][:10]:
                lines.append(f"| {r['title']} | {_fmt(r['views'])} | "
                             f"{_fmt(r['likes'])} | {_fmt(r['comments'])} |")
        else:
            lines.append("_No uploads yet._")

    if learned:
        lines += ["\n## 🧠 What the factory learned this week", "",
                  "These biases are now baked into every new video automatically:", ""]
        for name, note in learned:
            lines.append(f"- **{name}** — {note}")
    else:
        lines += ["\n## 🧠 Self-tuning", "",
                  "Warming up (needs 3+ measured videos per channel before the "
                  "bias engine activates)."]

    lines += ["\n_This issue is your hands-off dashboard. The only human task "
              "that pays: reply to comments once in a while._"]
    return "\n".join(lines)


def main() -> int:
    md = build_markdown()
    if is_ci():
        import subprocess
        proc = subprocess.run(["gh", "issue", "create",
                               "--title", "📊 Weekly Empire Report",
                               "--body-file", "-"],
                              input=md, capture_output=True, text=True)
        log("issue created: " + proc.stdout.strip() if proc.returncode == 0
            else "issue failed: " + proc.stderr[:300])
        return proc.returncode
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
