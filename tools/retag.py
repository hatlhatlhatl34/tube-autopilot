#!/usr/bin/env python3
"""Retag / delete an already-uploaded video (v3.2 ops tool).

Fixes metadata on videos that are already live or queued (publishAt),
without re-rendering anything. Quota cost: 1 unit (videos.list) + 50
(videos.update) per retag, 50 per delete.

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
    yt = youtube._service(cfg)

    if args.delete:
        yt.videos().delete(videoId=args.delete).execute()
        log(f"🗑 deleted {args.delete}")
        return 0

    if not (args.video and (args.title or args.description)):
        ap.error("need --video plus --title or --description, or --delete ID")

    cur = yt.videos().list(part="snippet", id=args.video).execute()
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
    yt.videos().update(part="snippet",
                       body={"id": args.video, "snippet": sn}).execute()
    log(f"✅ retagged {args.video}:")
    log(f"   old: {old}")
    log(f"   new: {sn['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
