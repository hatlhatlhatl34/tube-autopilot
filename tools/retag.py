#!/usr/bin/env python3
"""Retag / delete an already-uploaded video (v3.2 ops tool).

Fixes metadata on videos that are already live or queued (publishAt),
without re-rendering anything. Quota cost: 1 unit (videos.list) + 50
(videos.update) per retag, 50 per delete.

SCOPE NOTE: videos.update / videos.delete require the force-ssl scope.
Refresh tokens minted before v3.2 carry only upload+readonly, so on
those this tool prints RETAG-SCOPE and exits cleanly. The one-time
fix: run `python tools/setup_wizard.py --redo <channel>` (the wizard
now requests force-ssl too), Allow, and paste the new FACTORY_ENV
block into GitHub → Settings → Secrets → Actions. Daily uploads never
needed this scope and are unaffected either way.

Run it from the Actions tab via .github/workflows/retag.yml, or
locally with factory.env present:

  python tools/retag.py --video VIDEO_ID --title "New title"
  python tools/retag.py --video VIDEO_ID --title "T" --description "D"
  python tools/retag.py --delete VIDEO_ID
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_channel          # noqa: E402
from src.utils import log                    # noqa: E402

FORCE_SSL = "https://www.googleapis.com/auth/youtube.force-ssl"


def _scope_help(channel: str, exc: Exception) -> int:
    log("RETAG-SCOPE: the stored refresh token cannot mint a force-ssl")
    log(f"access token ({type(exc).__name__}: {str(exc)[:200]})")
    log(f"Fix (one time): python tools/setup_wizard.py --redo {channel}")
    log("  → Allow → paste the printed FACTORY_ENV block into GitHub →")
    log("  Settings → Secrets → Actions → FACTORY_ENV. Retagging unlocks")
    log("  from then on; uploads never needed this scope.")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="retag or delete an uploaded video")
    ap.add_argument("--channel", default="mindset")
    ap.add_argument("--video", help="video id to retag")
    ap.add_argument("--title", help="new title")
    ap.add_argument("--description", help="new description (optional)")
    ap.add_argument("--delete", help="video id to DELETE")
    args = ap.parse_args()

    cfg = load_channel(args.channel)
    from src import youtube

    try:
        yt = youtube._service(cfg, scopes=[FORCE_SSL])
    except Exception as e:
        return _scope_help(args.channel, e)

    from googleapiclient.errors import HttpError

    if args.delete:
        try:
            yt.videos().delete(id=args.delete).execute()
            log(f"🗑 deleted {args.delete}")
            return 0
        except HttpError as e:
            if e.resp.status == 403 and "scope" in str(e).lower():
                return _scope_help(args.channel, e)
            log(f"✗ delete failed: HTTP {e.resp.status} — {str(e)[:200]}")
            return 1

    if not (args.video and (args.title or args.description)):
        ap.error("need --video plus --title or --description, or --delete ID")

    try:
        cur = yt.videos().list(part="snippet", id=args.video).execute()
    except HttpError as e:
        if e.resp.status == 403 and "scope" in str(e).lower():
            return _scope_help(args.channel, e)
        log(f"✗ videos.list failed: HTTP {e.resp.status} — {str(e)[:200]}")
        return 1

    items = cur.get("items") or []
    if not items:
        log(f"✗ video {args.video} not found")
        return 1
    sn = items[0]["snippet"]
    old = sn.get("title", "")
    if args.title:
        sn["title"] = args.title[:100]
    if args.description:
        sn["description"] = args.description
    try:
        yt.videos().update(part="snippet",
                           body={"id": args.video, "snippet": sn}).execute()
    except HttpError as e:
        if e.resp.status == 403 and "scope" in str(e).lower():
            return _scope_help(args.channel, e)
        log(f"✗ update failed: HTTP {e.resp.status} — {str(e)[:200]}")
        return 1
    log(f"✅ retagged {args.video}:")
    log(f"   old: {old}")
    log(f"   new: {sn['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
