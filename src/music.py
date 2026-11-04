"""Music — 100% original, synthesized ambient pads (copyright-safe by construction).

Each channel mood maps to a chord progression; tracks are generated with
numpy sines + envelopes at low volume, so the voice always sits on top.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from .utils import log, note_freq

SR = 44100

PROGRESSIONS = {
    "epic":    [["A2", "E3", "A3", "C#4"], ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3"]],
    "curious": [["C3", "G3", "E4"], ["G2", "D3", "B3"], ["A2", "E3", "C4"], ["F2", "C3", "A3"]],
    "neon":    [["E2", "B2", "E3", "G3"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3"], ["D3", "A3", "D4", "F#4"]],
    "wealth":  [["A2", "E3", "A3"], ["G2", "D3", "G3", "B3"], ["F2", "C3", "F3", "A3"], ["E2", "B2", "E3", "G#3"]],
}
PROG_LEN = 4  # seconds per chord


def make_track(cfg: dict, duration: float, out_path: Path) -> Path:
    mood = cfg.get("music_mood", "curious")
    prog = PROGRESSIONS.get(mood, PROGRESSIONS["curious"])
    total = max(int(SR * duration), SR)
    audio = np.zeros(total, dtype=np.float64)
    n_chords = int(np.ceil(duration / PROG_LEN))

    for ci in range(n_chords):
        chord = prog[ci % len(prog)]
        t0 = int(ci * PROG_LEN * SR)
        t1 = min(int((ci + 1) * PROG_LEN * SR) + SR // 2, total)  # slight overlap
        n = t1 - t0
        if n <= 0:
            break
        t = np.arange(n) / SR
        env = np.minimum(t / 1.1, 1.0) * np.minimum((n / SR - t) / 1.4, 1.0)
        env = np.clip(env, 0, 1)
        chord_sig = np.zeros(n)
        for note in chord:
            f = note_freq(note)
            for mult, amp in ((1.0, 1.0), (2.0, 0.28), (3.0, 0.08)):
                det = 1.0 + (0.0012 if mult == 1.0 else 0.0)
                chord_sig += amp * np.sin(2 * np.pi * f * mult * det * t)
                chord_sig += amp * np.sin(2 * np.pi * f * mult * (2 - det) * t) * 0.6
        audio[t0:t1] += env * chord_sig * 0.18

    # gentle stereo widening + fades
    fade = int(SR * 1.2)
    if total > 2 * fade:
        audio[:fade] *= np.linspace(0, 1, fade)
        audio[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(audio)) or 1.0
    audio = audio / peak * 0.30
    left = audio
    right = np.concatenate([np.zeros(SR // 50), audio[:-SR // 50]])

    stereo = np.empty(total * 2)
    stereo[0::2] = left
    stereo[1::2] = right
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    log(f"   track: mood={mood} | {duration:.1f}s | chords={n_chords}")
    return out_path
