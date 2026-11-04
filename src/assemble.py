"""Assembler — turns backgrounds + voice + captions + music into a finished Short.

Pipeline per video:
  1. render one Ken Burns clip per scene (zoompan, alternating in/out)
  2. concat scene clips (stream copy, same codec params)
  3. mux voice + music, burn word-synced ASS captions
"""
from __future__ import annotations

import math
from pathlib import Path

from .config import FPS, FONTS_DIR, frame_size
from .utils import ffmpeg, ffprobe_duration, log

ZOOM_MAX = 1.16


def _scene_clip(bg: Path, dur: float, out: Path, zoom_in: bool,
                w: int, h: int, crf: int = 21) -> None:
    frames = max(10, round(dur * FPS))
    zr = f"{(ZOOM_MAX - 1.0) / frames:.6f}"
    if zoom_in:
        zexpr = f"min(zoom+{zr},{ZOOM_MAX})"
    else:
        zexpr = f"if(eq(on,0),{ZOOM_MAX},max(1.001,zoom-{zr}))"
    sw, sh = int(w * 1.25), int(h * 1.25)
    vf = (
        f"[0:v]scale={sw}:{sh},"
        f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={w}x{h}:fps={FPS},format=yuv420p[v]"
    )
    ffmpeg(["-i", str(bg), "-filter_complex", vf, "-map", "[v]",
            "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast",
            "-crf", str(crf), "-r", str(FPS), str(out)])


def render(cfg: dict, work: Path, scene_times: list[tuple[float, float]],
           backgrounds: list[Path], ass_path: Path, voice: Path, music: Path) -> Path:
    video = cfg.get("mode") == "video"
    w, h = frame_size(cfg)
    # 1. scene clips — each clip runs until the NEXT scene starts, so the
    #    body timeline stays identical to the voice timeline (sentence
    #    pauses included). Without this, concat squeezes the pauses out,
    #    the body ends seconds before the voice, and -shortest would cut
    #    the narration tail mid-word.
    clips = []
    n = len(scene_times)
    for i, (start, end) in enumerate(scene_times):
        dur = (scene_times[i + 1][0] - start) if i + 1 < n else (end - start)
        dur = max(dur, 0.4)
        bg = backgrounds[i % len(backgrounds)]
        clip = work / f"scene_{i:02d}.mp4"
        _scene_clip(bg, dur, clip, zoom_in=(i % 2 == 0), w=w, h=h)
        clips.append(clip)
        log(f"   scene {i + 1}/{n}: {dur:.1f}s {'zoom-in' if i % 2 == 0 else 'zoom-out'}")

    # tail card: hold last background 1.5s so the outro always fully lands
    tail = work / "scene_tail.mp4"
    _scene_clip(backgrounds[(len(scene_times)) % len(backgrounds)], 1.5, tail,
                zoom_in=True, w=w, h=h)

    # 2. concat
    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{c.name}'\n" for c in clips + [tail]))
    body = work / "body.mp4"
    ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])

    # 3. audio + captions
    final = work / "final.mp4"
    fc = (
        f"[1:a]volume=1.30,aresample=44100[voc];"
        f"[2:a]volume=0.16,aresample=44100[mus];"
        f"[voc][mus]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[aout];"
        f"[0:v]subtitles={ass_path.name}:fontsdir={FONTS_DIR}[vout]"
    )
    ffmpeg(["-i", str(body), "-i", str(voice), "-i", str(music),
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            "-shortest", str(final)], cwd=str(work))

    dur = ffprobe_duration(str(final))
    log(f"   final: {final.name} | {dur:.1f}s | {final.stat().st_size / 1e6:.1f} MB")
    lo, hi = (40.0, 220.0) if video else (12.0, 65.0)
    if not (lo <= dur <= hi):
        kind = "long-form video" if video else "Shorts"
        raise RuntimeError(f"final duration {dur:.1f}s outside healthy {kind} range {lo}-{hi}s")
    return final
