"""Visuals — procedurally generated backgrounds (1080x1920) and thumbnails (1280x720).

Zero external assets: every frame is generated from the channel's palette,
so uploads are 100% copyright-safe and visually on-brand every day.
"""
from __future__ import annotations

import colorsys
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import font_path, frame_size
from .utils import clean_text


def _hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i: i + 2], 16) for i in (0, 2, 4))


def _shift(rgb: tuple[int, int, int], deg: float) -> tuple[int, int, int]:
    r, g, b = (x / 255 for x in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + deg / 360.0) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def _vertical_gradient(size: tuple[int, int], stops: list[tuple[int, int, int]]) -> Image.Image:
    w, hgt = size
    ys = np.linspace(0, 1, hgt)
    top = np.array(stops[0], dtype=float)
    mid = np.array(stops[len(stops) // 2], dtype=float)
    bot = np.array(stops[-1], dtype=float)
    rows = np.zeros((hgt, 3))
    first = hgt // 2
    rows[:first] = top + (mid - top) * (ys[:first] * 2)[:, None]
    rows[first:] = mid + (bot - mid) * ((ys[first:] - 0.5) * 2)[:, None]
    arr = np.repeat(rows[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def make_backgrounds(cfg: dict, n: int, out_dir: Path, seed: int = 0) -> list[Path]:
    """n variants of the channel background, each subtly different.
    Renders at the channel's current frame size (vertical Shorts or the
    16:9 long-form canvas) so both formats stay perfectly on-brand."""
    rng = random.Random(seed)
    W, H = frame_size(cfg)  # shadows module constants with the right canvas
    pal = cfg["palette"]
    top, mid, bot = _hex2rgb(pal["bg_top"]), _hex2rgb(pal["bg_mid"]), _hex2rgb(pal["bg_bottom"])
    accent = _hex2rgb(pal["accent"])

    paths = []
    for i in range(n):
        t = i / max(1, n - 1) if n > 1 else 0
        hue_shift = (t - 0.5) * 18  # ±9° hue variety across scenes
        img = _vertical_gradient((W, H), [_shift(top, hue_shift), _shift(mid, hue_shift), _shift(bot, hue_shift)])

        # bokeh glow layer
        bokeh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(bokeh)
        for _ in range(cfg.get("bokeh", 24)):
            r = rng.randint(50, 240)
            x, y = rng.randint(-120, W + 120), rng.randint(-120, H + 120)
            a = rng.randint(16, 52)
            c = accent if rng.random() < 0.75 else (255, 255, 255)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (a,))
        bokeh = bokeh.filter(ImageFilter.GaussianBlur(18))
        img = Image.alpha_composite(img.convert("RGBA"), bokeh)

        # vignette
        vig = Image.new("L", (W, H), 0)
        dv = ImageDraw.Draw(vig)
        dv.ellipse([-W * 0.35, -H * 0.18, W * 1.35, H * 1.18], fill=255)
        vig = vig.filter(ImageFilter.GaussianBlur(240))
        black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        img = Image.composite(img, Image.alpha_composite(img, black), vig)

        # grain
        arr = np.asarray(img.convert("RGB")).astype(np.int16)
        noise = rng.randint(0, 1 << 30)
        gen = np.random.default_rng(noise)
        arr = np.clip(arr + gen.normal(0, 5, arr.shape), 0, 255).astype(np.uint8)
        out = out_dir / f"bg_{i:02d}.png"
        Image.fromarray(arr).save(out)
        paths.append(out)
    return paths


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def _fit_lines(text: str, font_file: str, start_size: int, min_size: int,
               max_w: int, max_lines: int, draw: ImageDraw.ImageDraw) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Shrink font until the whole text fits in max_lines — text is NEVER cut off."""
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_file, size)
        lines = _wrap(text, font, max_w, draw)
        if len(lines) <= max_lines:
            return font, lines
        size -= max(8, start_size // 10)
    font = ImageFont.truetype(font_file, min_size)
    return font, _wrap(text, font, max_w, draw)[:max_lines]


def _fit_right(draw, right_x, text, font, fill, y):
    w = draw.textlength(text, font=font)
    draw.text((right_x - w, y), text, font=font, fill=fill)


def _thumb_base(cfg: dict) -> tuple[Image.Image, ImageDraw.ImageDraw, tuple, tuple]:
    """Shared thumbnail canvas: gradient + glow + grain."""
    TW, TH = 1280, 720
    pal = cfg["palette"]
    img = _vertical_gradient((TW, TH), [_hex2rgb(pal["bg_top"]), _hex2rgb(pal["bg_mid"]), _hex2rgb(pal["bg_bottom"])])

    glow = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    accent = _hex2rgb(pal["accent"])
    dg.ellipse([TW // 2 - 430, TH // 2 - 300, TW // 2 + 430, TH // 2 + 300], fill=accent + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    # subtle grain for texture (less compression banding)
    arr = np.asarray(img.convert("RGB")).astype(np.int16)
    gen = np.random.default_rng(7)
    arr = np.clip(arr + gen.normal(0, 4, arr.shape), 0, 255).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")
    return img, ImageDraw.Draw(img), accent, (TW, TH)


def _shadow_text(draw, xy, text, font, fill, shadow=(0, 0, 0, 210), off=8):
    x, y = xy
    draw.text((x + off, y + off), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def make_thumbnail(cfg: dict, script: dict, out_path: Path, variant: int = 0) -> Path:
    """1280x720 branded thumbnail — 3 rotating layouts.

    (Same 16:9 canvas for Shorts and long-form videos — YouTube uses it for
    both. The corner chip tells viewers which format to expect.)

    variant 0: centered hero headline, one word highlighted with the accent color
    variant 1: giant-number stack (facts-style) with diagonal accent slash
    variant 2: split-band — big text up top, accent band with channel name below
    """
    img, draw, accent, (TW, TH) = _thumb_base(cfg)
    pal = cfg["palette"]
    text = clean_text(script.get("thumbnail_text") or script.get("title", "WATCH NOW"))[:34].upper()
    chip = "FULL VIDEO" if cfg.get("mode") == "video" else "DAILY DROP"

    black_font = str(font_path("Archivo Black"))

    if variant == 1 and text and text[0].isdigit():
        # ---------------- variant 1: number stack ----------------
        num = text[0]
        rest = text[1:].strip(" .:-—")
        num_font = ImageFont.truetype(black_font, 300)
        # headline: shrink-to-fit, max 2 lines, ends well above the bottom
        head_font, lines = _fit_lines(rest, black_font, 110, 70, TW - 200, 2, draw) if rest \
            else (ImageFont.truetype(black_font, 110), [])
        line_h = 124
        y = 430
        _shadow_text(draw, (70, 80), num, num_font, (255, 255, 255, 255), off=10)
        for ln in lines:
            _shadow_text(draw, (74, y), ln, head_font, (255, 255, 255, 255))
            y += line_h
        # brand top-right, never collides with the giant number
        brand_font = ImageFont.truetype(black_font, 44)
        _fit_right(draw, TW - 70, cfg["display_name"].upper(), brand_font, accent + (255,), 66)
        # small accent slash, bottom-left
        slash = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
        ds = ImageDraw.Draw(slash)
        ds.polygon([(0, TH), (210, TH), (0, TH - 210)], fill=accent + (255,))
        img = Image.alpha_composite(img, slash)
    elif variant == 2:
        # ---------------- variant 2: split band ----------------
        head_font, lines = _fit_lines(text, black_font, 130, 80, TW - 160, 2, draw)
        band_h = 170
        y = 80
        for ln in lines:
            _shadow_text(draw, (84, y), ln, head_font, (255, 255, 255, 255), off=10)
            y += 160
        band = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
        db = ImageDraw.Draw(band)
        db.polygon([(0, TH - band_h), (TW, TH - band_h), (TW, TH), (0, TH)],
                   fill=accent + (255,))
        img = Image.alpha_composite(img, band)
        draw = ImageDraw.Draw(img)
        # brand name auto-shrinks so name + tag ALWAYS fit side by side
        name = cfg["display_name"].upper()
        tag = chip
        tag_font = ImageFont.truetype(black_font, 40)
        tag_w = draw.textlength(tag, font=tag_font)
        size = 76
        while size >= 40:
            nf = ImageFont.truetype(black_font, size)
            if 70 + draw.textlength(name, font=nf) + 50 + tag_w + 70 <= TW:
                break
            size -= 6
        name_font = ImageFont.truetype(black_font, size)
        draw.text((70, TH - band_h + 30), name, font=name_font, fill=(10, 10, 10, 255))
        draw.text((TW - tag_w - 70, TH - band_h + 44), tag, font=tag_font, fill=(10, 10, 10, 210))
    else:
        # ---------------- variant 0: centered hero ----------------
        head_font, lines = _fit_lines(text, black_font, 150, 84, TW - 220, 3, draw)
        line_h = int(head_font.size * 1.12)
        total_h = len(lines) * line_h
        y = (TH - total_h) // 2 + 18
        hl_line = len(lines) // 2          # highlight a word on the middle line
        for i, ln in enumerate(lines):
            wpx = draw.textlength(ln, font=head_font)
            x = (TW - wpx) // 2
            if i == hl_line:
                words = ln.split()
                if len(words) >= 2:        # accent-box the longest word
                    hot_idx = max(range(len(words)), key=lambda k: len(words[k]))
                    hot = words[hot_idx]
                    before = " ".join(words[:hot_idx])
                    after = " ".join(words[hot_idx + 1:])
                    hw = draw.textlength(hot, font=head_font)
                    hx = x + (draw.textlength(before + " ", font=head_font) if before else 0)
                    draw.rounded_rectangle([hx - 16, y - 8, hx + hw + 16, y + head_font.size + 14],
                                            radius=20, fill=accent + (255,))
                    if before:
                        _shadow_text(draw, (x, y), before, head_font, (255, 255, 255, 255))
                    draw.text((hx, y), hot, font=head_font, fill=(12, 12, 12, 255))
                    if after:
                        _shadow_text(draw, (hx + hw + 24, y), after, head_font, (255, 255, 255, 255))
                else:
                    _shadow_text(draw, (x, y), ln, head_font, (255, 255, 255, 255))
            else:
                _shadow_text(draw, (x, y), ln, head_font, (255, 255, 255, 255))
            y += line_h
        # channel badge top-left (auto-shrink)
        badge_text = cfg["display_name"].upper()
        size = 52
        while size >= 30:
            bf = ImageFont.truetype(black_font, size)
            if 64 + draw.textlength(badge_text, font=bf) + 52 <= 760:
                break
            size -= 6
        label_font = ImageFont.truetype(black_font, size)
        bw = draw.textlength(badge_text, font=label_font)
        draw.rounded_rectangle([64, 58, 64 + bw + 48, 58 + size + 34], radius=24, fill=accent + (255,))
        draw.text((88, 62), badge_text, font=label_font, fill=(10, 10, 10, 255))
        # bottom-right chip
        tag_font = ImageFont.truetype(black_font, 38)
        tag = chip
        tw = draw.textlength(tag, font=tag_font)
        draw.rounded_rectangle([TW - tw - 104, TH - 92, TW - 56, TH - 40], radius=12,
                               fill=accent + (255,))
        draw.text((TW - tw - 96, TH - 96), tag, font=tag_font, fill=(10, 10, 10, 255))

    img.convert("RGB").save(out_path, "JPEG", quality=90)
    return out_path
