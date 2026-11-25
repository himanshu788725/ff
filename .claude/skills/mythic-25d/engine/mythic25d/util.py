"""Shared helpers: paths, colours, easing, deterministic RNG, hashing."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import subprocess
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
DATA_DIR = PKG_DIR / "data"
FONT_DIR = PKG_DIR / "fonts"
CACHE_DIR = Path(os.environ.get("MYTHIC_CACHE", Path.home() / ".cache" / "mythic25d"))

# --------------------------------------------------------------------------- colour

NAMED = {
    # folk-art paint box (Kalamkari / Pattachitra / Cheriyal inspired)
    "ink": "#2a1a10", "ink2": "#3b2616", "cream": "#f1e2bf", "bone": "#e8d8b4",
    "paper": "#e6d3a8", "ochre": "#d39b3a", "mustard": "#e2b448", "gold": "#e0ad3c",
    "gold_dk": "#b07d22", "saffron": "#e8843a", "vermilion": "#c63f28", "red": "#b8321f",
    "maroon": "#7a2318", "rose": "#d9776b", "pink": "#e59aa8", "lotus": "#e98aa0",
    "indigo": "#2f3a72", "navy": "#1f2850", "peacock": "#1d6d78", "teal": "#3f8f8a",
    "mint": "#9fd8c2", "leaf": "#4f7d3a", "leaf_dk": "#2f5428", "olive": "#7f7b3a",
    "sky": "#8db7c9", "krishna": "#3f7fb8", "rama": "#4f97b5", "shiva": "#9ab8c8",
    "skin_tan": "#c98a55", "skin_light": "#e2ae7c", "skin_brown": "#a8693e", "skin_dark": "#7a4a2c",
    "monkey": "#d99a3e", "bear": "#5a4636", "white": "#f6efdf", "black": "#1b120c",
    "grey": "#8a8478", "silver": "#c9c6bb", "violet": "#6d4a8c", "purple": "#563066",
    "green": "#3d7a4a", "emerald": "#2f8a62", "turquoise": "#3fa3a0", "brown": "#7a4b2a",
    "wood": "#8a5a32", "stone": "#9b8f7c", "snow": "#eef0ea", "smoke": "#6b625a",
    "fire": "#f09a2a", "flame": "#ffcf4a", "blood": "#8e1d16", "night": "#1a2240",
}


def rgb(c, a=None):
    """Accept '#rrggbb', named colour, (r,g,b) or (r,g,b,a); return tuple."""
    if isinstance(c, str):
        c = NAMED.get(c, c)
        c = c.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        t = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
        if len(c) == 8:
            t = t + (int(c[6:8], 16),)
    else:
        t = tuple(int(v) for v in c)
    if a is not None:
        return t[:3] + (int(a),)
    if len(t) == 3:
        return t + (255,)
    return t


def mix(c1, c2, t):
    a, b = rgb(c1), rgb(c2)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


def shade(c, k):
    """k<0 darken toward ink, k>0 lighten toward cream."""
    return mix(c, "#1b120c" if k < 0 else "#fff6e0", abs(k))


def hexc(c):
    r, g, b, *_ = rgb(c)
    return f"#{r:02x}{g:02x}{b:02x}"


# --------------------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def window(t, t0, t1, fade=0.25):
    """1 inside [t0,t1] with smooth edges of length fade."""
    if t < t0 - fade or t > t1 + fade:
        return 0.0
    if t < t0:
        return smooth((t - (t0 - fade)) / fade)
    if t > t1:
        return smooth(((t1 + fade) - t) / fade)
    return 1.0


EASES = {"linear": lambda t: clamp(t), "smooth": smooth, "inout": ease_in_out,
         "out": ease_out, "in": ease_in, "back": ease_back}


# --------------------------------------------------------------------------- misc

def rng(*seed_parts) -> random.Random:
    h = hashlib.sha1(repr(seed_parts).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def stable_hash(obj) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def need_bin(name):
    p = shutil.which(name)
    if not p:
        raise SystemExit(f"[mythic] '{name}' not found on PATH. Install it (see references/troubleshooting.md).")
    return p


def run(cmd, quiet=True, check=True):
    """Run a command list; raise with stderr tail on failure."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        tail = "\n".join((r.stderr or "").strip().splitlines()[-25:])
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(map(str, cmd[:6]))} ...\n{tail}")
    if not quiet:
        print(r.stdout)
    return r


def ffprobe_duration(path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
             "default=nw=1:nk=1", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def code_version(*names):
    """Hash of engine source files: cached sprites/envs rebuild automatically when code changes."""
    h = hashlib.sha1()
    for n in names:
        try:
            h.update((PKG_DIR / f"{n}.py").read_bytes())
        except OSError:
            pass
    return h.hexdigest()[:10]


def fmt_time(t):
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}:{s:05.2f}"
