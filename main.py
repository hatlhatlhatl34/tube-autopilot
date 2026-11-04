#!/usr/bin/env python3
"""tube-autopilot v3 — daily pipeline entrypoint.

Usage:
  python main.py --channel mindset            # one channel
  python main.py --channel all                # every channel
  python main.py --channel facts --dry-run    # render everything, skip upload/history
  python main.py --channel tech --offline     # skip trends (banks only, fully offline)
  python main.py --verify-only                # zero-quota post-publish verification pass

The v3 doctrine: writing = content banks ONLY (no AI API); voice =
local Kokoro (offline); the only external services are YouTube
(upload, own credentials) and GitHub (state).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import traceback

from src import assemble, captions, history, metadata, music, scriptwriter, trends, tts, visuals
from src.config import CHANNEL_IDS, load_channel, work_dir
from src.utils import is_dry_run, log, step


def run_channel(channel_id: str, offline: bool = False, no_upload: bool = False,
                 mode_override: str = "auto") -> dict:
    cfg = load_channel(channel_id)
    work = work_dir(channel_id)
    rng = random.Random()  # fresh entropy daily; banks + seeds keep variety
    t_start = time.time()
    deferred = None

    daily = int(cfg.get("daily_uploads", 1))
    done_today = history.count_today(channel_id)
    if done_today >= daily and not (is_dry_run() or no_upload):
        log(f"\n✅ {cfg['display_name']}: {done_today}/{daily} videos already shipped today — done for today.")
        return {"channel": channel_id, "video_id": None, "skipped": "daily target reached"}
    slot = done_today + 1

    # slot typing: the day's last upload is the long-form 16:9 video
    longform_slot = int(cfg.get("longform_slot", 0) or 0)
    if mode_override != "auto":
        mode = mode_override
    else:
        mode = "video" if (longform_slot and slot >= longform_slot) else "short"
    cfg["mode"] = mode

    kind = "LONG-FORM VIDEO (16:9)" if mode == "video" else "Short (9:16)"
    log(f"\n{'=' * 64}\n🚀  {cfg['display_name']}  ({channel_id}) — upload #{slot} of {daily} today — {kind}\n{'=' * 64}")

    with step("topic", f"Pick today's topic ({cfg['trends'].get('mode', 'theme')} mode, slot {slot})"):
        topic = {"topic": None, "source": "offline", "headlines": []}
        if not offline:
            topic = trends.pick_topic(cfg, rng, slot=slot)
        log(f"   topic: {topic['topic']}  [{topic['source']}]")

    with step("script", "Write the script"):
        script = scriptwriter.write_script(cfg, topic, rng)
        log(f"   source: {script['source']} | {len(script['scenes'])} scenes | "
            f"~{sum(len(s.split()) for s in script['scenes'])} words")
        log(f"   title: {script['title']}")
    with step("tts", "Synthesize neural voiceover"):
        voice_mp3, words, _ = tts.synthesize(cfg, script, work)

    with step("captions", "Build word-synced captions + scene timing"):
        s_times = captions.scene_times(script, words)
        ass = captions.build_ass(script, words, cfg, work / "captions.ass")
        total = captions.total_duration(script, words)
        log(f"   {len(s_times)} scenes | narration {total:.1f}s")

    with step("visuals", "Generate backgrounds + thumbnail"):
        bgs = visuals.make_backgrounds(cfg, min(4, len(s_times)), work, seed=random.randint(0, 1 << 30))
        import datetime as _dt
        variant = (_dt.date.today().timetuple().tm_yday + slot) % 3  # rotate layouts
        thumb = visuals.make_thumbnail(cfg, script, work / "thumbnail.jpg", variant=variant)
        log(f"   thumbnail variant: {['hero+highlight', 'number stack', 'split band'][variant]}")

    with step("music", "Synthesize copyright-free track"):
        music_wav = music.make_track(cfg, total + 1.0, work / "music.wav")

    with step("render", "Render final Short"):
        final = assemble.render(cfg, work, s_times, bgs, ass, voice_mp3, music_wav)

    with step("seo", "Assemble SEO metadata"):
        meta = metadata.build(cfg, script, topic)
        log(f"   title: {meta['title']}")
        log(f"   tags ({len(meta['tags'])}): {', '.join(meta['tags'][:10])}…")

    video_id = None
    dry = is_dry_run() or no_upload
    if dry:
        with step("upload", "DRY RUN — skipping upload"):
            log("   set DRY_RUN=0 (or drop --dry-run) to publish for real")
    else:
        from src import youtube
        with step("upload", f"Upload to YouTube ({cfg.get('visibility', 'public')})"):
            try:
                video_id = youtube.upload(cfg, final, meta, thumb_path=thumb)
            except youtube.UploadDeferred as d:
                # a quota-family deferral is a HEALTHY skip, not a failure:
                # the stamp is already in history, the next window self-heals
                log(f"   ⏸ {d}")
                log("   the rendered video is saved as an artifact; the next "
                    "slot retries automatically")
                video_id = None
                deferred = d.reason

    if not dry and video_id:
        with step("history", "Record topic in history (anti-repeat)"):
            history.record(channel_id, topic.get("topic") or script["topic"],
                           meta["title"], video_id, slot=slot,
                           hook_pattern=script.get("hook_pattern"))

    if not dry and not deferred:
        with step("verify", "Post-publish oEmbed probe (zero quota)"):
            from src import verify
            verify.run_channel(channel_id)

    (work / "script.json").write_text(json.dumps(
        {"channel": channel_id, "slot": slot, "topic": topic, "script": script,
         "meta": meta, "video_id": video_id, "thumbnail_variant": variant,
         "words": len(words), "duration": total,
         "hook_pattern": script.get("hook_pattern"),
         "ai_tells": script.get("tells", {}).get("total", 0),
         "deferred": deferred}, indent=1))

    log(f"\n✅ {cfg['display_name']} finished in {time.time() - t_start:.0f}s "
        f"→ {work / 'final.mp4'}")
    return {"channel": channel_id, "video_id": video_id, "work": str(work),
            "deferred": deferred}


def main() -> int:
    ap = argparse.ArgumentParser(description="tube-autopilot daily pipeline")
    ap.add_argument("--channel", default="all", help=f"one of {CHANNEL_IDS} or 'all'")
    ap.add_argument("--dry-run", action="store_true", help="render but never upload")
    ap.add_argument("--offline", action="store_true", help="skip trends + AI, use banks")
    ap.add_argument("--no-upload", action="store_true", help="render + metadata only")
    ap.add_argument("--mode", choices=["auto", "short", "video"], default="auto",
                    help="force render mode (auto: last slot of the day = long-form video)")
    ap.add_argument("--verify-only", action="store_true",
                    help="run only the zero-quota post-publish verification pass")
    args = ap.parse_args()

    if args.dry_run:
        import os
        os.environ["DRY_RUN"] = "1"

    ids = CHANNEL_IDS if args.channel == "all" else [args.channel]

    if args.verify_only:
        from src import verify
        total = verify.run_all(ids)
        if total["alerts"]:
            print("\n" + "\n".join(total["alerts"]))
            return 2            # alerts = actionable, but never a render failure
        return 0

    failures = []
    for cid in ids:
        try:
            run_channel(cid, offline=args.offline, no_upload=args.no_upload,
                        mode_override=args.mode)
        except Exception:
            log(f"\n❌ channel '{cid}' FAILED:\n{traceback.format_exc()}")
            failures.append(cid)
    if failures:
        log(f"\n💥 {len(failures)} channel(s) failed: {', '.join(failures)}")
        return 1
    log("\n🏁 all channels done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
