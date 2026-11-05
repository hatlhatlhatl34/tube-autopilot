"""Topic memory — data/history/<channel>.json, committed back by the workflow.

Prevents the system from repeating topics and gives you a permanent,
human-readable log of everything ever published.

v3 hardening (ported from the forever-factory's ledger doctrine):
  * .bak ladder — every save first promotes the last-known-good file
    to <channel>.json.bak; a corrupt main file falls back to .bak on
    load instead of silently resetting the channel's memory (the
    "total amnesia" 5-year hole);
  * defer stamps — a quota/upload deferral records WHY and UNTIL WHEN
    in <channel>.defer.json, so the gate and the pipeline skip
    cheaply instead of re-rendering against a dead window;
  * verified stamps — the post-publish oEmbed pass (src/verify.py)
    marks entries the probe actually SAW public;
  * hook_pattern — the previous video's hook pattern, so the hook
    rotation never repeats the same rhythm twice in a row.

v3.1 (2026-11-05) — THE ANTI-DUPLICATE LEDGER (owner caught two
twin shorts live on the channel):
  * `lines` — every entry now records the actual content lines spoken
    (quote / lessons / hook / outro, normalized). `recent_lines()`
    feeds the banks' exclusion windows so no line re-appears inside
    its rotation window;
  * `fingerprint` — sha1 of the sorted normalized line set. TWO
    IDENTICAL VIDEOS ARE NOW MATHEMATICALLY IMPOSSIBLE: the
    scriptwriter checks `fingerprint_seen()` before upload and
    re-rolls the script on collision. This is the ABSOLUTE rule the
    owner asked about — it checks ALL history, not a window.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import time
from pathlib import Path

from .config import HISTORY_DIR


def _path(channel_id: str) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR / f"{channel_id}.json"


def _bak_path(channel_id: str) -> Path:
    return HISTORY_DIR / f"{channel_id}.json.bak"


def _load(channel_id: str) -> list:
    """Read history with the .bak ladder: corrupt main file falls
    back to the last-known-good backup — never a silent reset."""
    for p in (_path(channel_id), _bak_path(channel_id)):
        if not p.exists():
            continue
        try:
            return json.loads(p.read_text())
        except Exception:
            continue
    return []


def _save(channel_id: str, entries: list) -> None:
    """The .bak ladder: the backup is written FIRST with the FULL new
    state (last-known-good = latest, never one save behind — a corrupt
    main file loses nothing), then the main file. A .bak write failure
    is non-fatal: the main save must go on."""
    payload = json.dumps(entries, indent=1, ensure_ascii=False)
    try:
        _bak_path(channel_id).write_text(payload)
    except Exception:
        pass
    _path(channel_id).write_text(payload)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())[:60]


def norm_line(s: str) -> str:
    """Normalize a content line for memory/fingerprint purposes.
    Longer than _norm's 60-char cap: fingerprint must see whole lines,
    or near-identical lines would hash differently."""
    return " ".join((s or "").lower().split())[:100]


def fingerprint_lines(lines: list[str]) -> str:
    """Stable content fingerprint: sha1 over the sorted normalized line
    set. Two videos with identical spoken content produce the same
    fingerprint — order-independent (scene order alone doesn't count
    as different content)."""
    seen, out = set(), []
    for ln in lines or []:
        n = norm_line(ln)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    blob = "\n".join(sorted(out))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def recent_topics(channel_id: str, n: int = 120) -> set[str]:
    return {_norm(e.get("topic", "")) for e in _load(channel_id)[-n:]}


def recent_lines(channel_id: str, n_entries: int) -> set[str]:
    """Every content line used in the last n_entries videos (the
    anti-repeat exclusion window). Old entries recorded before v3.1
    carry no `lines` — they're simply skipped, never treated as fresh."""
    out: set[str] = set()
    for e in _load(channel_id)[-n_entries:]:
        for ln in e.get("lines") or []:
            n = norm_line(ln)
            if n:
                out.add(n)
    return out


def fingerprint_seen(channel_id: str, fp: str) -> bool:
    """The ABSOLUTE no-duplicate rule: has this exact content ever been
    published on this channel? Checks ALL entries — no window."""
    if not fp:
        return False
    return any(e.get("fingerprint") == fp for e in _load(channel_id))


def recent_hook_patterns(channel_id: str, n: int = 3) -> set[str]:
    """Patterns of the last n videos' hooks — rotation now avoids the
    last THREE rhythms, not just the previous one."""
    out: set[str] = set()
    for e in _load(channel_id)[-n:]:
        p = e.get("hook_pattern")
        if p:
            out.add(p)
    return out


def seen(channel_id: str, topic: str) -> bool:
    return _norm(topic) in recent_topics(channel_id)


def published_today(channel_id: str) -> str | None:
    """Video id already uploaded by this channel today (duplicate-upload guard)."""
    today = datetime.date.today().isoformat()
    for e in reversed(_load(channel_id)):
        if e.get("date") == today and e.get("video_id"):
            return e["video_id"]
    return None


def count_today(channel_id: str) -> int:
    """How many videos this channel already shipped today (multi-upload support)."""
    today = datetime.date.today().isoformat()
    return sum(1 for e in _load(channel_id)
               if e.get("date") == today and e.get("video_id"))


def last_hook_pattern(channel_id: str) -> str | None:
    """Pattern of the most recent shipped video's hook (rotation input)."""
    for e in reversed(_load(channel_id)):
        if e.get("hook_pattern"):
            return e["hook_pattern"]
    return None


def record(channel_id: str, topic: str, title: str, video_id: str | None,
           slot: int | None = None, hook_pattern: str | None = None,
           publish_at: str | None = None, lines: list[str] | None = None,
           fingerprint: str | None = None) -> None:
    """Append an entry. publish_at is set for grid-scheduled videos —
    it is BOTH the booking mark (the grid skips slots it finds here)
    and the verify pass's "not late, just waiting" evidence.
    v3.1: lines + fingerprint power the anti-repeat windows and the
    absolute duplicate guard."""
    entries = _load(channel_id)
    entry = {
        "date": datetime.date.today().isoformat(),
        "slot": slot,
        "topic": topic[:200],
        "title": title[:200],
        "video_id": video_id,
        "hook_pattern": hook_pattern,
        "verified": False,
    }
    if lines:
        entry["lines"] = [norm_line(ln) for ln in lines
                          if norm_line(ln)][:16]
    if fingerprint:
        entry["fingerprint"] = fingerprint
    if publish_at:
        entry["publish_at"] = publish_at
    entries.append(entry)
    entries = entries[-500:]  # keep the file bounded
    _save(channel_id, entries)


def booked_slots(channel_id: str) -> set[str]:
    """The publishAt slots already booked by past runs (ISO strings).
    Grid booking input: a slot found here is taken, whatever happened
    to the video — a failed upload leaves the topic in anti-repeat
    history but never a phantom booking."""
    return {e["publish_at"] for e in _load(channel_id) if e.get("publish_at")}


# ── defer stamps (the Oct-7 forever-factory lesson) ─────────────────
def _defer_path(channel_id: str) -> Path:
    return HISTORY_DIR / f"{channel_id}.defer.json"


def set_defer(channel_id: str, reason: str, until_ts: float) -> None:
    """Record WHY an upload deferred and UNTIL WHEN the window is dead.
    The gate and pipeline consult this instead of re-rendering into a
    wall. Self-expiring: readers ignore stamps in the past."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    _defer_path(channel_id).write_text(json.dumps(
        {"reason": reason, "until": until_ts}))


def get_defer(channel_id: str) -> tuple[str | None, float]:
    """(reason, until_ts) of the ACTIVE defer stamp, else (None, 0)."""
    try:
        d = json.loads(_defer_path(channel_id).read_text())
    except Exception:
        return None, 0.0
    until = float(d.get("until") or 0)
    if until > time.time():
        return d.get("reason"), until
    return None, 0.0


def clear_defer(channel_id: str) -> None:
    _defer_path(channel_id).unlink(missing_ok=True)


# ── verified stamps (post-publish oEmbed evidence) ─────────────────
def mark_verified(channel_id: str, video_id: str) -> None:
    """Stamp an entry as CONFIRMED public by the zero-quota probe."""
    entries = _load(channel_id)
    for e in reversed(entries):
        if e.get("video_id") == video_id:
            e["verified"] = True
            break
    _save(channel_id, entries)


def recent_entries(channel_id: str, days: int = 10) -> list[dict]:
    """Entries from the last N days that carry a video id (verify input)."""
    today = datetime.date.today()
    out = []
    for e in _load(channel_id):
        d = e.get("date") or ""
        if not e.get("video_id") or not d:
            continue
        try:
            age = (today - datetime.date.fromisoformat(d)).days
        except ValueError:
            continue
        if 0 <= age <= days:
            out.append(e)
    return out
