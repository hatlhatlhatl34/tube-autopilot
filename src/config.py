"""Configuration loading and path resolution."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = ROOT / "channels"
ASSETS = ROOT / "assets"
FONTS_DIR = ASSETS / "fonts"
WORK = ROOT / "work"
HISTORY_DIR = ROOT / "data" / "history"


def _load_env_files() -> None:
    """Merge factory.env / .env (repo root) into os.environ.

    - factory.env: written by tools/setup_wizard.py on the owner's machine
    - .env: written by GitHub Actions from the single FACTORY_ENV secret
    Values already present in the environment win; empty placeholders
    (GitHub renders unset secrets as "") get filled in. This is what lets
    the whole network run with ONE repository secret.
    """
    for name in ("factory.env", ".env"):
        path = ROOT / name
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = val
        except Exception:
            pass


_load_env_files()

W, H, FPS = 1080, 1920, 30          # vertical Shorts
VW, VH = 1920, 1080                 # 16:9 long-form videos
CHANNEL_IDS = ["mindset", "facts", "tech", "money"]


def frame_size(cfg: dict) -> tuple[int, int]:
    """Render size for this run: Shorts are 1080x1920 vertical; the daily
    long-form video (cfg['mode'] == 'video') renders 1920x1080 landscape."""
    return (VW, VH) if cfg.get("mode") == "video" else (W, H)

_FONT_FILES = {
    "Anton": FONTS_DIR / "Anton-Regular.ttf",
    "Archivo Black": FONTS_DIR / "ArchivoBlack-Regular.ttf",
}
_FONT_FALLBACKS = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
]


def font_path(family: str) -> Path:
    """Resolve a bundled font file with system fallback."""
    if family in _FONT_FILES and _FONT_FILES[family].exists():
        return _FONT_FILES[family]
    for fb in _FONT_FALLBACKS:
        if fb.exists():
            return fb
    raise RuntimeError(f"no usable font found for family '{family}'")


def load_channel(channel_id: str) -> dict:
    path = CHANNELS_DIR / f"{channel_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"unknown channel '{channel_id}' (expected one of {CHANNEL_IDS})")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["id"] = channel_id
    cfg.setdefault("visibility", "public")
    cfg.setdefault("caption_font", "Anton")
    cfg.setdefault("caption_size", 92)
    cfg.setdefault("trends", {})
    cfg.setdefault("hashtags", ["#shorts"])
    cfg.setdefault("title_patterns", [])
    cfg.setdefault("bokeh", 24)
    cfg.setdefault("daily_uploads", 1)
    cfg.setdefault("longform_slot", 0)      # 0 = no daily long-form video
    cfg.setdefault("mode", "short")
    return cfg


def work_dir(channel_id: str) -> Path:
    import datetime
    d = WORK / channel_id / datetime.date.today().isoformat()
    d.mkdir(parents=True, exist_ok=True)
    return d


# v3 (2026-11-05): the Gemini path was REMOVED by the owner's no-API
# rule — scripts are written exclusively from the content banks
# (src/content_bank.py). The only external services this factory
# touches are the YouTube Data API (upload, own OAuth credentials)
# and GitHub (Actions + state).
