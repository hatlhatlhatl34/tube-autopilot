"""Voiceover — the engine ladder (v3: the forever-factory doctrine).

PRIMARY ENGINE: Kokoro-82M — vendored in assets/voice_kokoro/ — a
local, offline neural TTS (MIT license, CPU ~2x realtime). No API,
no key, no account, no network: the voice cannot go dark while the
repo exists. Per-channel personas:
    mindset  am_michael   (epic, grounded male)
    facts    af_bella     (bright, curious female)
    tech     am_onyx      (deep, steady tech narrator)
    money    bm_george    (authoritative British male)

FALLBACK ENGINE: edge-tts — the free neural service behind the Edge
browser's read-aloud (no key). Used only if the Kokoro files are ever
missing/broken, so quality stays neural. Fail-open doctrine: a missing
model degrades to a voice, never to silence. Strict no-network runs
can set allow_edge_fallback: false in the channel yaml.

Word timings (the karaoke-caption clock):
  * edge-tts — WordBoundary events (exact).
  * Kokoro — the int8 model exposes no duration output, so narration
    is synthesized PART BY PART (hook / scenes / outro) with each
    part's EXACT measured duration; words inside a part are placed
    proportionally to spoken length (chars + punctuation pause
    weight). Scene boundaries are therefore exact (scene_times slices
    on part boundaries) and per-word error stays around ±80 ms —
    invisible on 3-word caption cards.

Human prosody (both engines): per-video speed jitter ±2%, seeded from
the script text — every video breathes slightly differently, no
metronome cadence. (The forever-factory's per-sentence jitter is the
deeper upgrade; this keeps the whole-text pipeline intact.)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from .utils import clean_text, log

KOKORO_DIR = Path(__file__).resolve().parent.parent / "assets" / "voice_kokoro"
KOKORO_MODEL = "kokoro-v1.0.int8.onnx"
KOKORO_VOICES = "voices-v1.0.bin"
_PART_PAUSE = 0.28          # seconds of silence between hook/scenes/outro


def kokoro_available() -> bool:
    return (KOKORO_DIR / KOKORO_MODEL).exists() and (KOKORO_DIR / KOKORO_VOICES).exists()


class _KokoroEngine:
    """Lazy singleton — one model load per process."""
    _inst = None

    @classmethod
    def get(cls):
        if cls._inst is None:
            from kokoro_onnx import Kokoro
            cls._inst = Kokoro(str(KOKORO_DIR / KOKORO_MODEL),
                               str(KOKORO_DIR / KOKORO_VOICES))
        return cls._inst


# ── proportional word placement (Kokoro timing) ─────────────────────
_PAUSE_WEIGHT = {".": 3, "!": 3, "?": 3, ",": 2, ";": 2, ":": 1, "—": 2, "-": 1}


def _place_words(words: list[dict], text: str, start_s: float, dur_s: float) -> None:
    """Distribute word timings inside a part's exact measured span,
    proportional to spoken length (chars + trailing-punctuation pause)."""
    toks = text.split()
    if not toks:
        return
    weights = [len(t) + 1 + _PAUSE_WEIGHT.get(t[-1], 0) for t in toks]
    total = float(sum(weights))
    t = start_s
    for tok, w in zip(toks, weights):
        wd = (w / total) * dur_s
        words.append({
            "word": clean_text(tok),
            "offset_ms": round(t * 1000.0, 1),
            "duration_ms": round(wd * 1000.0, 1),
        })
        t += wd


def _kokoro_synth(cfg: dict, parts: list[str], out_dir: Path,
                  full_text: str) -> tuple[Path, list[dict]]:
    import numpy as np
    import soundfile as sf

    kokoro = _KokoroEngine.get()
    voice = cfg.get("kokoro_voice", "am_michael")
    base_speed = float(cfg.get("kokoro_speed", 0.97))

    # per-video prosody jitter, seeded from the script text (stable)
    seed = int(hashlib.sha256(full_text.encode()).hexdigest()[:8], 16)
    jitter = ((seed % 200) - 100) / 5000.0          # ±2.0 %
    speed = max(0.5, min(1.6, base_speed * (1.0 + jitter)))

    words: list[dict] = []
    clips: list = []
    sr = 24_000
    t_cursor = 0.0
    for part in parts:
        audio, sr = kokoro.create(part, voice=voice, speed=speed)
        audio = np.asarray(audio, dtype="float32")
        dur = len(audio) / sr
        _place_words(words, part, t_cursor, dur)
        clips.append(audio)
        clips.append(np.zeros(int(_PART_PAUSE * sr), dtype="float32"))
        t_cursor += dur + _PART_PAUSE

    # natural tail instead of a full trailing pause
    if clips:
        clips[-1] = clips[-1][: int(0.12 * sr)]
    audio = np.concatenate(clips)

    out_wav = out_dir / "voice.wav"
    sf.write(str(out_wav), audio, sr)
    return out_wav, words


# ── edge-tts fallback (exact WordBoundary timings) ──────────────────
async def _edge_stream(text: str, voice: str, rate: str, out_mp3: Path):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, volume="+0%",
                                boundary="WordBoundary")
    audio = bytearray()
    words: list[dict] = []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "word": clean_text(chunk["text"]),
                "offset_ms": chunk["offset"] / 10_000,
                "duration_ms": chunk["duration"] / 10_000,
            })
    if not audio:
        raise RuntimeError("edge-tts returned no audio")
    out_mp3.write_bytes(bytes(audio))
    return words


def _edge_synth(cfg: dict, out_dir: Path, full_text: str) -> tuple[Path, list[dict]]:
    out_mp3 = out_dir / "voice.mp3"
    words = asyncio.run(_edge_stream(
        full_text, cfg.get("voice", "en-US-GuyNeural"),
        cfg.get("voice_rate", "+0%"), out_mp3,
    ))
    return out_mp3, words


# ── public entrypoint ───────────────────────────────────────────────
def synthesize(cfg: dict, script: dict, out_dir: Path) -> tuple[Path, list[dict], str]:
    """Returns (voice_path, word_timings, full_spoken_text).

    Engine ladder: Kokoro (local, offline) -> edge-tts (config-gated
    fallback) -> loud error. Never silently robotic.
    """
    parts = [script["hook"], *script["scenes"], script["outro"]]
    parts = [clean_text(p) for p in parts if clean_text(p)]
    full_text = " ".join(parts)

    engine_cfg = cfg.get("voice_engine", "auto")
    if engine_cfg in ("auto", "kokoro") and kokoro_available():
        try:
            out_path, words = _kokoro_synth(cfg, parts, out_dir, full_text)
            log(f"   voice: kokoro:{cfg.get('kokoro_voice', 'am_michael')} "
                f"(offline) | {len(words)} words | {out_path.stat().st_size // 1024} KB")
            (out_dir / "words.json").write_text(json.dumps(words, indent=1))
            return out_path, words, full_text
        except Exception as exc:
            if not cfg.get("allow_edge_fallback", True):
                raise RuntimeError(f"kokoro voice failed and edge fallback "
                                   f"is disabled: {exc}") from exc
            log(f"   ⚠ kokoro failed ({type(exc).__name__}: {exc}) — "
                f"falling back to edge-tts")

    if engine_cfg in ("auto", "edge"):
        out_path, words = _edge_synth(cfg, out_dir, full_text)
        log(f"   voice: edge:{cfg.get('voice', 'en-US-GuyNeural')} "
            f"| {len(words)} words | {out_path.stat().st_size // 1024} KB")
        (out_dir / "words.json").write_text(json.dumps(words, indent=1))
        return out_path, words, full_text

    raise RuntimeError(
        f"no voice engine available (voice_engine={engine_cfg!r}, "
        f"kokoro files present={kokoro_available()})")
