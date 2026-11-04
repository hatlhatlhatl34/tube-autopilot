"""Post-publish verification — the verification-before-completion
skill, ported from the forever-factory (batch-3, 2026-11-01) and
adapted to the 4-channel history format.

The skill's Iron Law: "no completion claims without fresh verification
evidence." A recorded video id only ever meant the upload API
ACCEPTED it — never that the video actually went public. This pass
closes that gap:

  * entries from the last N days with a video id get probed via the
    YouTube oEmbed endpoint — anonymous, free, ZERO API quota;
  * a video the probe SEES public is stamped in history
    (entry["verified"] = True) — live evidence only, never
    blanket-true;
  * an entry older than the grace window that is STILL not public
    prints a VERIFY-ALERT marker — the workflow's alert step greps the
    marker and files a dated Issue (silence is the failure mode this
    exists to kill);
  * while a quota defer stamp is ACTIVE the channel is late ON
    PURPOSE — alerts are suppressed (stamps still collected).

Fail-open by design: any error (network, JSON, oEmbed outage) skips
quietly and retries next run — verification never starves the
pipeline. oEmbed answers non-200 for private videos AND for public
videos with embedding disabled; the rare unclear cases would be
settled by ONE videos.list call (1 unit) — left as a documented
option, default off (the strict no-diagnostics quota discipline).
"""
from __future__ import annotations

import datetime
import urllib.error
import urllib.request

from . import history
from .utils import log

_OEMBED = "https://www.youtube.com/oembed"
DEFAULT_GRACE_DAYS = 2
DEFAULT_SCAN_DAYS = 10


def oembed_public(video_id: str) -> bool | None:
    """The zero-quota probe. True = oEmbed saw it (public).
    False = 4xx (missing, private, or embeds-disabled). None = the
    probe itself could not answer (network/5xx) — never an alert."""
    url = (f"{_OEMBED}?url=https://www.youtube.com/watch?v={video_id}"
           f"&format=json")
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (factory verify)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 401, 403, 404):
            return False
        return None
    except Exception:
        return None


def run_channel(channel_id: str, *, grace_days: int = DEFAULT_GRACE_DAYS,
                scan_days: int = DEFAULT_SCAN_DAYS,
                probe=oembed_public) -> dict:
    """The verification pass for ONE channel. Prints its report + any
    VERIFY-ALERT markers; stamps confirmed-public videos into history.
    Returns a summary dict (tests assert on it). Never raises."""
    today = datetime.date.today()

    try:
        entries = history.recent_entries(channel_id, days=scan_days)
    except Exception:
        entries = []

    defer_reason, _ = history.get_defer(channel_id)
    confirmed = late = unknown = 0
    alerts: list[str] = []

    for e in entries:
        if e.get("verified"):
            confirmed += 1                     # stamped on a previous pass
            continue
        vid = e.get("video_id")
        verdict = probe(vid)
        if verdict is True:
            history.mark_verified(channel_id, vid)
            confirmed += 1
        elif verdict is False:
            try:
                age = (today - datetime.date.fromisoformat(e["date"])).days
            except Exception:
                continue
            if age > grace_days and not defer_reason:
                late += 1
                line = (f"VERIFY-ALERT [{channel_id}] '{(e.get('title') or '')[:40]}' "
                        f"— {vid} still not public {age}d after production "
                        f"(slot missed, stuck private, or removed)")
                alerts.append(line)
                print(line)
        else:
            unknown += 1                        # probe blind this run

    if unknown:
        print(f"[verify:{channel_id}] {unknown} video(s) not answerable "
              f"this pass — retried next run")
    if defer_reason:
        print(f"[verify:{channel_id}] defer stamp active ({defer_reason}) — "
              f"alerts suppressed, stamps still collected")
    print(f"[verify:{channel_id}] {confirmed} video(s) confirmed public, "
          f"{late} late past the {grace_days}-day grace window")
    return {"channel": channel_id, "confirmed": confirmed, "late": late,
            "unknown": unknown, "alerts": alerts}


def run_all(channel_ids: list[str], **kw) -> dict:
    total = {"confirmed": 0, "late": 0, "unknown": 0, "alerts": []}
    for cid in channel_ids:
        try:
            r = run_channel(cid, **kw)
        except Exception as exc:
            log(f"   [verify:{cid}] pass failed ({exc}) — fail-open")
            continue
        total["confirmed"] += r["confirmed"]
        total["late"] += r["late"]
        total["unknown"] += r["unknown"]
        total["alerts"].extend(r["alerts"])
    return total
