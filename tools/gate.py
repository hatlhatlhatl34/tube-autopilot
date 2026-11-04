#!/usr/bin/env python3
"""The per-channel daily gate — answers ONE question: should this
channel's pipeline run right now?

Ported from the forever-factory's gate doctrine (its Oct 2026 hardening:
GitHub cron slots get starved, so every workflow carries MANY staggered
slots; the gate makes every duplicate fire a 15-second free SKIP
instead of a re-render). Stdlib ONLY — no pip install: it costs the
runner seconds, not minutes.

Verdict (one line, exit 0 either way — SKIP is a HEALTHFUL outcome):
  SKIP  channel shipped its daily target already
  SKIP  quota defer stamp active (window is dead on purpose — retry later)
  RUN   today's target not met and no active defer
  RUN   --force (a human dispatch always wins)

Usage:
  python3 tools/gate.py --channel facts
  python3 tools/gate.py --all          # one line per channel: "<id> RUN|SKIP"
  python3 tools/gate.py --channel facts --force
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history"
CHANNELS = ("mindset", "facts", "tech", "money")

DAILY_DEFAULT = 1

# Frozen publishAt grids — a copy of the `schedule:` block in
# channels/<ch>.yaml. The gate runs BEFORE pip install, so it cannot
# read YAML (the forever-factory doctrine: freeze the grid here and
# KEEP THE TWO IN SYNC when a channel's grid changes).
GRIDS = {
    "mindset": {"tz": "Africa/Cairo",
                "slots": ["00:00", "06:00", "12:00", "18:00", "20:00"]},
}
GRID_MARGIN_MIN = 25     # mirror of src/youtube.py SLOT_MARGIN_MIN
GRID_HORIZON_H = 26      # mirror of src/youtube.py SLOT_HORIZON_H


def _load_history(ch: str) -> list:
    for p in (HISTORY / f"{ch}.json", HISTORY / f"{ch}.json.bak"):
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
            if isinstance(data, list):
                return data
        except Exception:
            continue
    return []


def _count_today(ch: str) -> int:
    today = datetime.date.today().isoformat()
    return sum(1 for e in _load_history(ch)
               if e.get("date") == today and e.get("video_id"))


def _daily_target(ch: str) -> int:
    """Read daily_uploads from the channel yaml WITHOUT yaml (stdlib
    gate): a one-line regex fallback, defaulting to the safe 1/day."""
    yml = ROOT / "channels" / f"{ch}.yaml"
    try:
        import re
        m = re.search(r"^\s*daily_uploads:\s*(\d+)", yml.read_text(), re.M)
        return int(m.group(1)) if m else DAILY_DEFAULT
    except Exception:
        return DAILY_DEFAULT


def _defer_active(ch: str) -> tuple[bool, str]:
    p = HISTORY / f"{ch}.defer.json"
    try:
        d = json.loads(p.read_text())
        if float(d.get("until") or 0) > time.time():
            return True, str(d.get("reason") or "deferred")
    except Exception:
        pass
    return False, ""


def _grid_free(ch: str) -> bool:
    """Is any publishAt slot in the next 26h still UNBOOKED?

    Mirrors src/youtube.py next_publish_slot() with the frozen grid:
    a slot is bookable when it is past the margin, inside the horizon,
    and NOT already present as an entry's publish_at in history.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    g = GRIDS[ch]
    tz = ZoneInfo(g["tz"])
    now = datetime.now(tz)
    used = {e.get("publish_at") for e in _load_history(ch)
            if e.get("publish_at")}
    for day_offset in (0, 1, 2):
        base = (now + timedelta(days=day_offset)).date()
        for hhmm in g["slots"]:
            hh, mm = map(int, hhmm.split(":"))
            s = datetime(base.year, base.month, base.day, hh, mm, tzinfo=tz)
            if (now + timedelta(minutes=GRID_MARGIN_MIN) < s
                    <= now + timedelta(hours=GRID_HORIZON_H)
                    and s.isoformat() not in used):
                return True
    return False


def verdict(ch: str, force: bool = False) -> str:
    if force:
        return f"RUN   {ch} — forced (human dispatch)"
    active, reason = _defer_active(ch)
    if active:
        return f"SKIP  {ch} — defer stamp active ({reason}); window self-heals"
    if ch in GRIDS:
        # GROWTH MODE: the grid is the day's target. RUN while a free
        # publishAt slot exists in the horizon; SKIP when it's full.
        if _grid_free(ch):
            return f"RUN   {ch} — free publishAt slot(s) in the next 26h"
        return f"SKIP  {ch} — publishAt grid fully booked (26h horizon)"
    done = _count_today(ch)
    target = _daily_target(ch)
    if done >= target:
        return f"SKIP  {ch} — {done}/{target} shipped today"
    return f"RUN   {ch} — {done}/{target} shipped today"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", choices=CHANNELS)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="bypass the gate (human dispatch always wins)")
    args = ap.parse_args()

    if args.all or not args.channel:
        for ch in CHANNELS:
            print(verdict(ch, force=args.force))
        return 0
    print(verdict(args.channel, force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
