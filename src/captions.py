"""Captions: word-timed ASS subtitles (viral 'karaoke' style) + scene timing.

Scene durations are derived from actual word offsets, so background cuts
always land exactly where narration segments change.
"""
from __future__ import annotations

from pathlib import Path

from .config import font_path, frame_size
from .utils import clean_text


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _segments(script: dict) -> list[tuple[str, int]]:
    """[(segment_text, word_count)] in spoken order."""
    segs = []
    for label in ("hook", "scenes", "outro"):
        if label == "scenes":
            for s in script["scenes"]:
                t = clean_text(s)
                if t:
                    segs.append((t, len(t.split())))
        else:
            t = clean_text(script[label])
            if t:
                segs.append((t, len(t.split())))
    return segs


def scene_times(script: dict, words: list[dict]) -> list[tuple[float, float]]:
    """Per-segment (start, end) seconds from real word timings."""
    segs = _segments(script)
    times = []
    idx = 0
    for _, n in segs:
        chunk = words[idx: idx + n]
        idx += n
        if not chunk:
            continue
        start = chunk[0]["offset_ms"] / 1000 - 0.18
        end = chunk[-1]["offset_ms"] / 1000 + chunk[-1]["duration_ms"] / 1000 + 0.15
        if times:
            start = max(start, times[-1][1] + 0.02)
        times.append((round(start, 3), round(end, 3)))
    return times


def build_ass(script: dict, words: list[dict], cfg: dict, out_path: Path) -> Path:
    """Write the .ass subtitle file with 2-3 word chunks, uppercase."""
    family = cfg.get("caption_font", "Anton")
    font_path(family)  # fail early if no font at all
    video = cfg.get("mode") == "video"
    res_x, res_y = frame_size(cfg)
    if video:
        # landscape: smaller captions, anchored near the bottom bar
        size = int(cfg.get("caption_size", 92) * 0.74)
        margin_v = 96
    else:
        size = cfg.get("caption_size", 92)
        margin_v = 470

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{family},{size},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,7,3,2,70,70,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    max_words = 3
    chunk: list[dict] = []

    def flush():
        if not chunk:
            return
        text = " ".join(w["word"] for w in chunk).upper()
        text = text.replace("{", "").replace("}", "")
        if text:
            start = chunk[0]["offset_ms"] / 1000
            end = chunk[-1]["offset_ms"] / 1000 + chunk[-1]["duration_ms"] / 1000
            events.append(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(end + 0.05)},Cap,,0,0,0,,"
                f"{{\\fad(50,50)}}{text}"
            )
        chunk.clear()

    for w in words:
        if chunk and (len(chunk) >= max_words or
                      (w["offset_ms"] - (chunk[-1]["offset_ms"] + chunk[-1]["duration_ms"])) > 400):
            flush()
        chunk.append(w)
    flush()

    out_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return out_path


def total_duration(script: dict, words: list[dict]) -> float:
    if not words:
        return 20.0
    last = words[-1]
    return last["offset_ms"] / 1000 + last["duration_ms"] / 1000 + 0.9
