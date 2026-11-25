"""Colour grading: presets applied in-engine (fast per-channel LUT + saturation)
and exportable as .cube 3D LUTs for Resolve / Premiere / ffmpeg lut3d.

Preset fields: contrast (S-curve), gamma (r,g,b), lift (shadow colour), gain
(highlight colour), sat (saturation), fade (black lift amount).
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageEnhance

GRADES = {
    "kathaa": dict(desc="Reference look: warm aged-paper puppet theatre, brown shadows, creamy highlights",
                   contrast=0.42, gamma=(0.98, 1.0, 1.06), lift=(30, 18, 10), gain=(255, 240, 214), sat=0.86),
    "kathaa_night": dict(desc="Night puppet stage: deep indigo shadows, warm lamp highlights",
                         contrast=0.45, gamma=(1.05, 1.02, 0.96), lift=(10, 12, 26), gain=(250, 236, 214), sat=0.82),
    "agni": dict(desc="Fire / yagya / burning Lanka: hot oranges, crushed warm shadows",
                 contrast=0.5, gamma=(0.92, 1.02, 1.15), lift=(34, 12, 6), gain=(255, 232, 196), sat=1.05),
    "rakt": dict(desc="Battlefield dusk: blood-red sky, smoky browns",
                 contrast=0.5, gamma=(0.95, 1.05, 1.1), lift=(36, 14, 12), gain=(250, 226, 200), sat=0.9),
    "neel": dict(desc="Moonlit blue night", contrast=0.4, gamma=(1.1, 1.02, 0.92), lift=(8, 12, 30),
                 gain=(226, 236, 255), sat=0.78),
    "swarna": dict(desc="Divine golden glow (darshan, avatars)", contrast=0.32, gamma=(0.94, 0.98, 1.12),
                   lift=(40, 28, 12), gain=(255, 246, 220), sat=0.95),
    "smriti": dict(desc="Flashback / memory: faded sepia", contrast=0.25, gamma=(1.0, 1.02, 1.1), lift=(46, 36, 26),
                   gain=(240, 226, 200), sat=0.45),
    "prabhat": dict(desc="Dawn: soft rose & gold", contrast=0.3, gamma=(0.96, 1.0, 1.02), lift=(30, 20, 22),
                    gain=(255, 238, 220), sat=0.9),
    "van": dict(desc="Forest: green-gold, earthy", contrast=0.4, gamma=(1.02, 0.98, 1.08), lift=(18, 22, 10),
                gain=(248, 244, 214), sat=0.88),
    "natural": dict(desc="Minimal grade", contrast=0.15, gamma=(1, 1, 1), lift=(8, 6, 4), gain=(255, 252, 246), sat=1.0),
}


def _curve(x, g):
    c = g["contrast"]
    y = x - c * np.sin(2 * np.pi * x) / (2 * np.pi)
    return np.clip(y, 0, 1)


@lru_cache(maxsize=16)
def lut_tables(name):
    g = GRADES.get(name, GRADES["kathaa"])
    x = np.linspace(0, 1, 256)
    tables = []
    for ch in range(3):
        y = _curve(x, g) ** g["gamma"][ch]
        lo, hi = g["lift"][ch] / 255.0, g["gain"][ch] / 255.0
        y = lo + y * (hi - lo)
        tables.extend((np.clip(y, 0, 1) * 255).astype(np.uint8).tolist())
    return tables


def apply_grade(img: Image.Image, name: str) -> Image.Image:
    if not name or name == "none":
        return img
    g = GRADES.get(name, GRADES["kathaa"])
    out = img.convert("RGB").point(lut_tables(name))
    if abs(g["sat"] - 1) > 0.01:
        out = ImageEnhance.Color(out).enhance(g["sat"])
    return out


def write_cube(name, path, size=33):
    g = GRADES[name]
    x = np.linspace(0, 1, size)
    with open(path, "w") as f:
        f.write(f'TITLE "mythic25d {name}"\nLUT_3D_SIZE {size}\n')
        for b in x:
            for gg in x:
                for r in x:
                    rgb = []
                    for ch, v in enumerate((r, gg, b)):
                        y = _curve(np.array([v]), g)[0] ** g["gamma"][ch]
                        lo, hi = g["lift"][ch] / 255.0, g["gain"][ch] / 255.0
                        rgb.append(lo + y * (hi - lo))
                    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                    rgb = [min(1, max(0, lum + (c - lum) * g["sat"])) for c in rgb]
                    f.write(f"{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n")
    return path


def ffmpeg_finish_filter(grain=6, sharpen=0.3, flicker=0.012):
    """Film finish used at master: temporal grain, gentle sharpen, lamp flicker."""
    parts = []
    if flicker > 0:
        parts.append(f"eq=brightness='{flicker}*sin(2*PI*t*1.7)+{flicker * 0.6}*sin(2*PI*t*4.3)':eval=frame")
    if sharpen > 0:
        parts.append(f"unsharp=5:5:{sharpen}:5:5:0")
    if grain > 0:
        parts.append(f"noise=c0s={grain}:c0f=t+u:c1s={max(1, grain // 3)}:c1f=t+u:c2s={max(1, grain // 3)}:c2f=t+u")
    return ",".join(parts)
