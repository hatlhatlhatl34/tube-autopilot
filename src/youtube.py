"""YouTube upload — Data API v3 with per-channel OAuth credentials.

**Recommended architecture (default):** each channel has its OWN Google
Cloud project → its own OAuth client → its own 10,000 daily quota units.
Secrets per channel: YT_CLIENT_ID_<CH>, YT_CLIENT_SECRET_<CH>,
YT_REFRESH_TOKEN_<CH>.

A shared-project setup (one client + one token set for all channels) still
works via the global YT_CLIENT_ID / YT_CLIENT_SECRET fallbacks — in that
case all channels share ONE 10,000-unit pool and the local quota ledger
keeps the network inside it.

Quota math: 1 upload = 1,600 units, thumbnail = 50 → 5 uploads/channel
(4 Shorts + 1 long-form video) = 8,250 of the 10,000 personal-project cap.
Comfortably free; the local ledger blocks anything past DAILY_LIMIT and the
YouTube API audit form can raise the cap if ever needed.
"""
from __future__ import annotations

import datetime
import json
import os
import time
from datetime import datetime as _dt, timedelta, timezone
from zoneinfo import ZoneInfo

from . import history
from .config import HISTORY_DIR
from .utils import log

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_URI = "https://oauth2.googleapis.com/token"

UPLOAD_UNITS = 1600
THUMB_UNITS = 50
DAILY_LIMIT = 9950          # hard stop under the 10,000 cap (5 uploads = 8,250)

_PACIFIC = ZoneInfo("America/Los_Angeles")


class UploadDeferred(RuntimeError):
    """Quota-family deferral — a HEALTHY skip, not a failure.

    Raised only AFTER the defer stamp is written to history, so the
    gate and the next runs skip cheaply instead of re-rendering into
    a dead window (the Oct-7 forever-factory lesson: silent 403s
    burned 3 full renders because nothing recorded WHY or UNTIL
    WHEN). The pipeline catches it, reports honestly, and the next
    window self-heals."""

    def __init__(self, reason: str, until_ts: float):
        super().__init__(f"uploads deferred ({reason}) until "
                         f"{_dt.fromtimestamp(until_ts, timezone.utc):%H:%M UTC}")
        self.reason = reason
        self.until_ts = until_ts


def _next_pacific_midnight() -> float:
    """Quota resets at midnight Pacific (DST-aware). +5 min margin."""
    now = _dt.now(_PACIFIC)
    nm = (now + timedelta(days=1)).replace(hour=0, minute=5,
                                            second=0, microsecond=0)
    return nm.timestamp()


def _reason_of(e) -> str:
    """The machine reason inside a YouTube HttpError body, if any."""
    try:
        raw = getattr(e, "content", b"") or b""
        body = json.loads(raw.decode() or "{}")
        return (body.get("error", {}).get("errors", [{}])[0]
                .get("reason", ""))
    except Exception:
        return ""


def quota_scope(cfg: dict) -> str:
    """'channel' if this channel has its own OAuth client, else 'shared'."""
    own = os.environ.get(f"YT_CLIENT_ID_{cfg['id'].upper()}")
    return cfg["id"] if own else "shared"


def _ledger() -> dict:
    p = HISTORY_DIR / "quota.json"
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def quota_used_today(scope: str) -> int:
    data = _ledger()
    entry = data.get(scope) or {}
    if entry.get("date") != datetime.date.today().isoformat():
        return 0
    return int(entry.get("used", 0))


def _charge_quota(scope: str, units: int) -> None:
    data = _ledger()
    today = datetime.date.today().isoformat()
    entry = data.get(scope) or {}
    if entry.get("date") != today:
        entry = {"date": today, "used": 0}
    entry["used"] = int(entry.get("used", 0)) + units
    data[scope] = entry
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    (HISTORY_DIR / "quota.json").write_text(json.dumps(data, indent=1))


def quota_ok(cfg: dict, cost: int = UPLOAD_UNITS + THUMB_UNITS) -> tuple[bool, int]:
    """Local guard so a shared-project setup can never hit the hard 403."""
    scope = quota_scope(cfg)
    used = quota_used_today(scope)
    return used + cost <= DAILY_LIMIT, used


def _credentials(cfg: dict):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    ch = cfg["id"].upper()
    cid = os.environ.get(f"YT_CLIENT_ID_{ch}") or os.environ.get("YT_CLIENT_ID")
    csec = os.environ.get(f"YT_CLIENT_SECRET_{ch}") or os.environ.get("YT_CLIENT_SECRET")
    rt = os.environ.get(f"YT_REFRESH_TOKEN_{ch}")
    if not (cid and csec and rt):
        raise RuntimeError(
            f"missing secrets for '{cfg['id']}' — set YT_CLIENT_ID_{ch}, "
            f"YT_CLIENT_SECRET_{ch} and YT_REFRESH_TOKEN_{ch} "
            "(or the global YT_CLIENT_ID / YT_CLIENT_SECRET fallbacks)"
        )
    creds = Credentials(token=None, refresh_token=rt, client_id=cid,
                        client_secret=csec, token_uri=TOKEN_URI, scopes=SCOPES)
    creds.refresh(Request())
    return creds


def _service(cfg: dict):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=_credentials(cfg), cache_discovery=False)


def upload(cfg: dict, video_path, meta: dict, thumb_path=None) -> str:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    ok, used = quota_ok(cfg)
    if not ok:
        reason = "dailyLimitExceeded (local ledger)"
        until = _next_pacific_midnight()
        history.set_defer(cfg["id"], reason, until)
        raise UploadDeferred(
            f"{reason} — '{quota_scope(cfg)}' project already used "
            f"~{used} units today", until)

    yt = _service(cfg)
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
        },
        "status": {
            "privacyStatus": cfg.get("visibility", "public"),
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")

    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    retries = 0
    rate_retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                log(f"   upload: {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in (500, 502, 503) and retries < 3:
                retries += 1
                time.sleep(3 * retries)
                continue
            reason = _reason_of(e)
            if e.resp.status == 403 and reason in ("quotaExceeded",
                                                   "dailyLimitExceeded"):
                until = _next_pacific_midnight()
                history.set_defer(cfg["id"], reason, until)
                _explain(e)
                raise UploadDeferred(reason, until) from e
            if e.resp.status == 403 and reason == "uploadLimitExceeded":
                # the rolling 24h uploads-per-day window: 2h back-off
                until = time.time() + 2 * 3600
                history.set_defer(cfg["id"], reason, until)
                _explain(e)
                raise UploadDeferred(reason, until) from e
            if e.resp.status == 403 and reason == "rateLimitExceeded" \
                    and rate_retries < 1:
                rate_retries += 1
                log("   ⚠ rate limited — waiting 90s, one retry")
                time.sleep(90)
                continue
            _explain(e, reason)
            raise
        except OSError:
            time.sleep(5)
            continue

    video_id = response["id"]
    _charge_quota(quota_scope(cfg), UPLOAD_UNITS)
    history.clear_defer(cfg["id"])       # a landing upload clears the stamp
    log(f"   uploaded: https://youtu.be/{video_id} (visibility={cfg.get('visibility')})")

    if thumb_path:
        try:
            yt.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumb_path), mimetype="image/jpeg"),
            ).execute()
            _charge_quota(quota_scope(cfg), THUMB_UNITS)
            log("   thumbnail set")
        except HttpError as e:
            log(f"   ⚠ thumbnail not set: {e.resp.status} (non-fatal)")
    return video_id


def _explain(e, reason: str = "") -> None:
    code = getattr(getattr(e, "resp", None), "status", 0)
    if reason in ("quotaExceeded", "dailyLimitExceeded"):
        log(f"   ✗ {reason} — daily quota exceeded (resets midnight Pacific; "
            f"deferred, next run self-heals).")
    elif reason == "uploadLimitExceeded":
        log("   ✗ uploadLimitExceeded — rolling upload window hit "
            "(2h back-off, deferred).")
    elif reason == "rateLimitExceeded":
        log("   ✗ rateLimitExceeded — throttled.")
    elif code == 403 and "quota" in str(e).lower():
        log("   ✗ quota-family 403 (unparsed reason) — deferred to be safe.")
    elif code == 401:
        log("   ✗ auth failed — refresh token may be revoked. Re-run tools/auth.py.")
    elif code == 400 and "invalidUpload" in str(e):
        log("   ✗ video rejected by YouTube. Check duration/format settings.")
    else:
        log(f"   ✗ YouTube API error {code}: {str(e)[:300]}")


def channel_stats(cfg: dict) -> dict:
    """Used by the weekly report."""
    yt = _service(cfg)
    ch = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
    item = ch["items"][0]
    stats = item["statistics"]
    uploads_playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]

    vids = yt.playlistItems().list(part="contentDetails", playlistId=uploads_playlist,
                                   maxResults=20).execute()
    ids = [v["contentDetails"]["videoId"] for v in vids.get("items", [])]
    rows = []
    if ids:
        details = yt.videos().list(part="snippet,statistics", id=",".join(ids)).execute()
        for v in details.get("items", []):
            s = v.get("statistics", {})
            rows.append({
                "video_id": v["id"],
                "title": v["snippet"]["title"][:60],
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
            })
    return {
        "name": item["snippet"]["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
        "recent": rows,
    }
