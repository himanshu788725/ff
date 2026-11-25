"""Frame renderer + chunked multi-process video encoder.

plan (from scene.compile_plan) -> frames -> ffmpeg chunks -> concat.
Per frame:  env layers (camera parallax) + hanging props + flames + water
+ birds + puppets (strings, shadow, rim glow) + front layer + light rig
(spot, god-rays, drifting haze, particles, vignette) + fx + curtain.
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from . import actions as A
from .catalog import get_entity
from .grade import apply_grade
from .envs import M, build_env, stage_unit
from .fauna import build_creature
from .gfx import Pen, Sprite, affine_paste, catmull, linear_gradient, noise, radial, soft_dot, blur_alpha_fast
from .props import build_prop, prop_bounds
from .puppet import build_character
from .rig import draw_strings
from .util import clamp, ease_in_out, lerp, mix, rgb, rng, shade, smooth, EASES

CHAR_HEIGHT = 0.6   # rig unit -> stage unit factor (100 rig units ~ 60% of a 16:9 frame)


# =========================================================================== camera

CAM_PRESETS = {
    # name:          zoom (start, end)   x (start, end)   y (start, end)
    "static": dict(z=(1.04, 1.04), x=(0.5, 0.5), y=(0.5, 0.5)),
    "push_in": dict(z=(1.0, 1.12), x=(0.5, 0.5), y=(0.5, 0.5)),
    "pull_out": dict(z=(1.14, 1.0), x=(0.5, 0.5), y=(0.5, 0.5)),
    "pan_left": dict(z=(1.1, 1.1), x=(0.57, 0.43), y=(0.5, 0.5)),
    "pan_right": dict(z=(1.1, 1.1), x=(0.43, 0.57), y=(0.5, 0.5)),
    "tilt_up": dict(z=(1.12, 1.12), x=(0.5, 0.5), y=(0.58, 0.45)),
    "tilt_down": dict(z=(1.12, 1.12), x=(0.5, 0.5), y=(0.45, 0.58)),
    "drift": dict(z=(1.04, 1.09), x=(0.49, 0.52), y=(0.5, 0.49)),
    "close_up": dict(z=(1.35, 1.42), x=(0.5, 0.5), y=(0.44, 0.44)),
    # reference-style 2.5D moves (strong parallax between layers)
    "truck_right": dict(z=(1.14, 1.14), x=(0.36, 0.64), y=(0.5, 0.5)),
    "truck_left": dict(z=(1.14, 1.14), x=(0.64, 0.36), y=(0.5, 0.5)),
    "crane_down": dict(z=(1.2, 1.12), x=(0.5, 0.5), y=(0.3, 0.52)),
    "crane_up": dict(z=(1.12, 1.2), x=(0.5, 0.5), y=(0.52, 0.3)),
    "establish": dict(z=(1.0, 1.3), x=(0.5, None), y=(0.5, None)),      # wide set -> push onto `on`
    "reveal": dict(z=(1.42, 1.0), x=(None, 0.5), y=(None, 0.5)),        # tight on `on` -> pull back to the set
    "push_to": dict(z=(1.08, 1.55), x=(0.5, None), y=(0.5, None)),     # slow push onto a face
    "follow": dict(z=(1.2, 1.2), x=(None, None), y=(None, None)),      # track a walking/flying character
    "float": dict(z=(1.06, 1.1), x=(0.49, 0.51), y=(0.5, 0.5)),        # dreamy handheld drift
    "dolly_zoom": dict(z=(1.0, 1.25), x=(0.5, None), y=(0.55, None)),
}
FRAMES = {"wide": 1.0, "full": 1.12, "medium": 1.32, "close": 1.6, "extreme": 2.0}


def camera_at(cam: dict, t, dur, target=None):
    """target(t) -> (x, y_frame_centre) of the `on:` character for the current framing."""
    move = cam.get("move", "drift")
    p = dict(CAM_PRESETS.get(move, CAM_PRESETS["drift"]))
    fz = FRAMES.get(cam.get("frame")) if cam.get("frame") else None
    z0 = cam.get("from", p["z"][0] if not fz or move in ("establish", "reveal", "push_to", "dolly_zoom") else fz)
    z1 = cam.get("to", p["z"][1] if not fz else fz)
    k = EASES.get(cam.get("ease", "inout"), ease_in_out)(clamp(t / max(0.01, dur)))
    tx = ty = None
    if target is not None:
        tx, ty = target(t)
    xs = list(cam.get("x", p["x"])) if isinstance(cam.get("x", p["x"]), (list, tuple)) else [cam["x"], cam["x"]]
    ys = list(cam.get("y", p["y"])) if isinstance(cam.get("y", p["y"]), (list, tuple)) else [cam["y"], cam["y"]]
    for arr, tv, dflt in ((xs, tx, 0.5), (ys, ty, 0.5)):
        for i in range(2):
            if arr[i] is None:
                arr[i] = tv if tv is not None else dflt
    if target is not None and "x" not in cam and move in ("static", "drift", "push_in", "pull_out", "close_up", "float"):
        xs = [lerp(xs[0], tx, 0.75), lerp(xs[1], tx, 0.75)]
        ys = [lerp(ys[0], ty, 0.6), lerp(ys[1], ty, 0.6)]
    z = lerp(z0, z1, k)
    x, y = lerp(xs[0], xs[1], k), lerp(ys[0], ys[1], k)
    if cam.get("breathe", True):          # the camera of the reference is never fully still
        b = 1.6 if move == "float" else 1.0
        x += b * (0.0022 * math.sin(0.31 * t + 1.3) + 0.0011 * math.sin(0.83 * t))
        y += b * (0.0016 * math.sin(0.23 * t + 0.4))
        z += b * 0.006 * (0.5 + 0.5 * math.sin(0.17 * t))
    return x, y, max(1.0, z)


def clamp_cam(x, y, z):
    lim = M + 0.5 - 0.5 / z
    return clamp(x, 0.5 - lim, 0.5 + lim), clamp(y, 0.5 - lim, 0.5 + lim), z


def eff_cam(cam, par):
    x, y, z = cam
    return 0.5 + (x - 0.5) * par, 0.5 + (y - 0.5) * par, 1 + (z - 1) * par


def to_screen(px, py, cam, par, W, H):
    ex, ey, ez = eff_cam(cam, par)
    return ((px - ex) * ez + 0.5) * W, ((py - ey) * ez + 0.5) * H, ez


def layer_view(img, cam, par, W, H):
    ex, ey, ez = eff_cam(cam, par)
    c = (ex + M - 0.5 / ez) * W
    f = (ey + M - 0.5 / ez) * H
    return img.transform((W, H), Image.AFFINE, (1 / ez, 0, c, 0, 1 / ez, f), resample=Image.BILINEAR)


# =========================================================================== flames, waves, light textures

@lru_cache(maxsize=64)
def flame_frames(size_px: int, kind="lamp", n=8):
    """Stylised folk flames (outer red, orange, yellow core) — n animation frames."""
    out = []
    S = size_px / 10.0
    tongues = {"lamp": 1, "yagya": 3, "camp": 3, "pyre": 4, "big": 5}.get(kind, 1)
    for f in range(n):
        r = rng("flame", kind, f)
        p = Pen((-6 * tongues ** 0.6 - 2, -14, 6 * tongues ** 0.6 + 2, 2), S)
        for layer, col, k in ((0, "#c8321f", 1.0), (1, "#f0882a", 0.72), (2, "#ffd34a", 0.45), (3, "#fff2c0", 0.2)):
            for tg in range(tongues):
                cx = (tg - (tongues - 1) / 2) * 3.4
                hh = (9.0 + r.uniform(-1.6, 1.6)) * (1.0 if tg == tongues // 2 else 0.78) * k
                ww = 3.4 * (0.7 + 0.3 * k)
                lean = r.uniform(-1.2, 1.2)
                pts = [(cx - ww, 0), (cx - ww * 0.9, -hh * 0.35), (cx - ww * 0.3 + lean * 0.5, -hh * 0.7),
                       (cx + lean, -hh), (cx + ww * 0.4 + lean * 0.5, -hh * 0.62), (cx + ww * 0.95, -hh * 0.3),
                       (cx + ww, 0)]
                p.poly(pts, fill=col, smooth=True, n=8)
        spr = p.finish(outline="#5a160c", ow=0.25, inner=0.05, texture=0.3)
        out.append(spr)
    return out


@lru_cache(maxsize=8)
def light_textures(W, H, spot, spot_color, vign, amb, haze, seed=0):
    spot_img = radial(W, H, spot[0] * W, spot[1] * H, 0.6 * math.hypot(W, H) / 2, rgb(spot_color, 255),
                      (0, 0, 0, 255), 1.0).convert("RGB")
    # vignette: warm dark brown edges (stage lit from above)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx / W - 0.5) * 1.0
    dy = (yy / H - 0.47) * 1.15
    d = np.sqrt(dx * dx + dy * dy) / 0.72
    m = np.clip(1 - vign * np.clip(d, 0, 1.3) ** 2.2, 0.05, 1) * amb
    top = np.clip(1 - (yy / H) / 0.42, 0, 1) ** 2          # fly-loft above the stage is darker
    m = m * (1 - 0.28 * top)
    tint = np.array([1.0, 0.93, 0.84], np.float32)
    wt = np.clip((1.0 - m / max(amb, 1e-3)) * 2.2, 0, 1)[..., None]          # smooth warm tint toward the edges
    vig = np.clip(m[..., None] * 255 * (1 - wt * (1 - tint)), 0, 255).astype(np.uint8)
    vig_img = Image.fromarray(vig, "RGB")
    # drifting haze texture (2x width) in haze colour
    qw, qh = max(16, W // 8 * 2), max(8, H // 8)
    hz = noise(qw, qh, max(6, qw // 10), 5, seed + 3)
    hz = np.clip((hz - 0.25) / 0.75, 0, 1) ** 1.6
    yv = np.linspace(0, 1, qh, dtype=np.float32)
    band = 0.35 + 0.65 * np.exp(-((yv - 0.62) / 0.28) ** 2)      # densest just above the ground line
    c = np.array(rgb(haze)[:3], np.float32)
    harr = (hz[..., None] * band[:, None, None] * c[None, None, :]).astype(np.uint8)
    haze_img = Image.fromarray(harr, "RGB").filter(ImageFilter.GaussianBlur(max(1.5, qw / 120)))
    haze_img = haze_img.resize((W * 2, H), Image.BICUBIC)
    # god rays from above
    rays = []
    for v in range(2):
        r = rng("rays", W, H, v)
        im = Image.new("L", (W, H), 0)
        d2 = ImageDraw.Draw(im)
        ox = spot[0] * W + r.uniform(-W * 0.1, W * 0.1)
        for _ in range(7):
            a = math.radians(r.uniform(62, 118))
            w0 = r.uniform(0.01, 0.05) * W
            L = H * 1.4
            ex, ey = ox + math.cos(a) * L, -H * 0.1 + math.sin(a) * L
            d2.polygon([(ox - w0 * 0.2, -H * 0.1), (ox + w0 * 0.2, -H * 0.1), (ex + w0, ey), (ex - w0, ey)],
                       fill=r.randint(40, 110))
        im = im.filter(ImageFilter.GaussianBlur(W / 60))
        col = Image.new("RGB", (W, H), rgb(spot_color)[:3])
        rays.append(ImageChops.multiply(col, Image.merge("RGB", (im, im, im))))
    return spot_img, vig_img, haze_img, rays


def wave_layers(env, W, H, n=4):
    """Pre-rendered animated wave line overlays (stepped like paper theatre)."""
    if not env.water:
        return []
    LW, LH = int(W * (1 + 2 * M)), int(H * (1 + 2 * M))
    out = []
    U = stage_unit(W, H)
    for f in range(n):
        im = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for wb in env.water:
            y0, y1 = (wb["y0"] + M) * H, min(LH, (wb["y1"] + M) * H)
            col = rgb(shade(wb["color"], 0.45))[:3]
            rows = max(2, int((y1 - y0) / (U * 2.4)))
            for j in range(rows):
                yy = y0 + (j + 0.5) * (y1 - y0) / rows
                per = U * (4.0 + 2.0 * j / rows)
                off = (f / n) * per + (j % 2) * per / 2
                rr = per * 0.42
                x = -per + off
                wpx = max(1, int(U * 0.22))
                while x < LW + per:
                    d.arc([x - rr, yy - rr * 0.6, x + rr, yy + rr * 0.6], 200, 340, fill=col + (150,), width=wpx)
                    x += per
        out.append((im, env.water[0].get("parallax", 1.0)))
    return out


# =========================================================================== particles

def draw_particles(frame, kind, t, W, H, density=1.0, seed=0):
    if not kind:
        return
    r = rng("particles", kind, seed)
    U = H / 1080
    if kind in ("dust", "stars"):
        n = int(70 * density)
        for i in range(n):
            x0, y0 = r.random(), r.random()
            sp = r.uniform(0.004, 0.012)
            x = (x0 + t * sp * r.choice((-1, 1)) + 0.01 * math.sin(t * 0.7 + i)) % 1
            y = (y0 - t * sp * 0.6) % 1
            tw = 0.5 + 0.5 * math.sin(t * r.uniform(1, 3) + i)
            rad = r.uniform(1.2, 3.2) * U
            dot = soft_dot(int(max(1, rad)), "#fff0c8" if kind == "dust" else "#e8e8ff", int(140 * tw))
            frame.alpha_composite(dot, (int(x * W), int(y * H)))
    elif kind == "embers":
        n = int(60 * density)
        for i in range(n):
            x0, ph = r.random(), r.random()
            life = r.uniform(3, 6)
            k = ((t / life) + ph) % 1
            x = (x0 + 0.04 * math.sin(t * 1.3 + i) + k * r.uniform(-0.05, 0.05)) % 1
            y = 1.05 - k * 1.1
            dot = soft_dot(int(max(1, r.uniform(1.5, 3.5) * U)), "#ffb04a", int(230 * (1 - k)))
            frame.alpha_composite(dot, (int(x * W), int(y * H)))
    elif kind == "fireflies":
        n = int(26 * density)
        for i in range(n):
            x = (r.random() + 0.03 * math.sin(t * 0.6 + i * 1.7)) % 1
            y = 0.35 + 0.55 * r.random() + 0.03 * math.cos(t * 0.8 + i)
            b = max(0.0, math.sin(t * r.uniform(1.5, 3) + i * 2.1)) ** 2
            dot = soft_dot(int(max(2, 4 * U)), "#e8ff9a", int(220 * b))
            frame.alpha_composite(dot, (int(x * W), int(y * H)))
    elif kind == "petals":
        d = ImageDraw.Draw(frame)
        n = int(28 * density)
        for i in range(n):
            x0, ph = r.random(), r.random()
            k = ((t / r.uniform(6, 10)) + ph) % 1
            x = (x0 + 0.08 * math.sin(t * 0.9 + i)) % 1 * W
            y = (-0.05 + k * 1.1) * H
            a = t * 2 + i
            rr = r.uniform(4, 8) * U
            pts = [(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.5), (x - math.cos(a) * rr, y - math.sin(a) * rr * 0.5)]
            d.line(pts, fill=rgb(r.choice(["#f2a2b8", "#f0882a", "#f2c94a"]), 220), width=max(2, int(4 * U)))
    elif kind == "snow":
        n = int(110 * density)
        for i in range(n):
            x0, ph = r.random(), r.random()
            k = ((t / r.uniform(5, 9)) + ph) % 1
            x = (x0 + 0.02 * math.sin(t + i)) % 1
            dot = soft_dot(int(max(1, r.uniform(1.5, 4) * U)), "#ffffff", 200, 0.5)
            frame.alpha_composite(dot, (int(x * W), int((k * 1.1 - 0.05) * H)))
    elif kind == "rain":
        d = ImageDraw.Draw(frame)
        n = int(160 * density)
        for i in range(n):
            x0, ph = r.random(), r.random()
            k = ((t / r.uniform(0.6, 0.9)) + ph) % 1
            x, y = (x0 + k * 0.05) * W, (k * 1.1 - 0.05) * H
            d.line([(x, y), (x - 6 * U, y + 26 * U)], fill=(200, 210, 220, 110), width=max(1, int(1.5 * U)))


def draw_birds(frame, n, t, W, H, seed=0, color="#2a1c14"):
    if n <= 0:
        return
    d = ImageDraw.Draw(frame)
    r = rng("birds", seed)
    U = H / 1080
    for i in range(n):
        speed = r.uniform(0.025, 0.05)
        x = (r.uniform(-0.2, 1.0) + t * speed) % 1.3 - 0.15
        y = r.uniform(0.08, 0.3) + 0.01 * math.sin(t * 1.3 + i)
        s = r.uniform(7, 12) * U
        fl = math.sin(t * r.uniform(7, 10) + i) * 0.6
        X, Y = x * W, y * H
        d.line([(X - s, Y - s * fl), (X - s * 0.45, Y - s * 0.2), (X, Y)], fill=rgb(color, 220), width=max(1, int(2 * U)),
               joint="curve")
        d.line([(X, Y), (X + s * 0.45, Y - s * 0.2), (X + s, Y - s * fl)], fill=rgb(color, 220), width=max(1, int(2 * U)),
               joint="curve")


# =========================================================================== performers

def _ppu_bucket(need):
    for b in (5.0, 7.0, 9.0, 12.0, 16.0, 22.0):
        if b >= need:
            return b
    return 22.0


LAYER_PAR = {"sky": 0.08, "far": 0.28, "mid": 0.55, "set": 0.82, "ground": 1.0, "front": 1.3}


def pop_light(canvas, light_col, H, glow=0.0, ambient=False, night=False, fade=1.0, depth=1.0):
    """The reference's 'lit puppet' look: a wide warm aura + a bright tight rim around the
    silhouette, light wrapping onto the edges, a saturation lift, and a soft drop shadow."""
    from PIL import ImageEnhance
    a = canvas.getchannel("A")
    W_, H_ = canvas.size
    k = (0.45 if ambient else 1.0) * fade * (1.0 if night else 0.8)
    col = rgb(light_col)[:3]
    warm = tuple(int(c * 0.55 + v * 0.45) for c, v in zip(col, (255, 226, 170) if night else (255, 236, 200)))
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    # soft drop shadow on the backdrop (down-right)
    sh = blur_alpha_fast(a, H * 0.009).point(lambda v: int(v * (0.32 if not night else 0.22) * (0.6 if ambient else 1)))
    sl = Image.new("RGBA", canvas.size, (18, 9, 3, 0))
    sl.putalpha(sh)
    out.alpha_composite(sl, (min(W_ - 1, int(H * 0.008)), min(H_ - 1, int(H * 0.006))))
    # wide aura + tight rim glow
    for rad, op in ((H * (0.03 + 0.03 * glow), 0.62 + 0.5 * glow), (H * 0.007, 0.95)):
        g = blur_alpha_fast(a, rad, down=4 if rad > 8 else 2).point(lambda v, o=op * k: int(min(255, v * o * 1.5)))
        gl = Image.new("RGBA", canvas.size, warm + (0,))
        gl.putalpha(g)
        out.alpha_composite(gl)
    # puppet itself, slightly more saturated & brighter than the set
    rgbp = canvas.convert("RGB")
    rgbp = ImageEnhance.Color(rgbp).enhance(1.14 if not ambient else 1.0)
    if depth >= 0.95 and not ambient:
        rgbp = ImageEnhance.Brightness(rgbp).enhance(1.05)
    # light wrap: backlight bleeding onto the silhouette edges
    inner = ImageChops.subtract(a, blur_alpha_fast(a, H * 0.006, down=2))
    wrap = Image.new("RGB", canvas.size, warm)
    rgbp = Image.composite(Image.blend(rgbp, ImageChops.screen(rgbp, wrap), 0.55 * k), rgbp,
                           inner.point(lambda v: min(255, int(v * 2.2))))
    pup = rgbp.convert("RGBA")
    pup.putalpha(a)
    out.alpha_composite(pup)
    return out


def life_casts(life, dur, ground, water, seed=0):
    """Expand ambient-life specs into performer configs with actions spanning the shot."""
    import random as _r
    out = []
    for i, L in enumerate(life):
        r = _r.Random(f"{seed}-{i}-{L['who']}")
        mode = L.get("mode", "graze")
        depth = float(L.get("depth", 0.7))
        # background life sits further back than its depth suggests: smaller & higher on the set
        base = {"who": L["who"], "depth": depth, "strings": False, "ambient": True,
                "scale": float(L.get("scale", 1.0)) * (0.55 + 0.45 * depth) ** 2}
        if L.get("y") is not None:
            base["y"] = float(L["y"])
        layer = "mid" if depth < 0.7 else "set"
        if mode in ("run_across", "walk_across", "march"):
            speed = float(L.get("speed", 0.25 if mode == "run_across" else 0.06))
            d = 1.5 / speed
            period = max(float(L.get("period", 12)), d * 0.35 if mode == "run_across" else 4.0)
            t0 = r.uniform(0.3, min(4.0, max(0.4, period * 0.4)))
            k = 0
            while t0 < dur:
                go_right = (k + r.randint(0, 1)) % 2 == 0
                x0, x1 = (-0.25, 1.25) if go_right else (1.25, -0.25)
                n = int(L.get("n", 1))
                for j in range(n):
                    off = j * 0.07 * (-1 if go_right else 1)
                    act = "run" if mode == "run_across" else "walk"
                    c = dict(base, x=x0 + off, face="right" if go_right else "left",
                             actions=[{"do": "hidden", "at": 0, "dur": t0}, {"do": act, "at": t0, "to": x1 + off, "dur": d,
                                                                             "steps": d * (3.2 if act == "run" else 1.6),
                                                                             "ease": False, "sfx": False}])
                    out.append((layer, c))
                t0 += d * (1.0 if mode != "run_across" else 0.6) + period
                k += 1
        elif mode == "graze":
            x = float(L.get("x", r.uniform(0.1, 0.9)))
            acts = []
            t = r.uniform(0.5, 2.0)
            while t < dur:
                acts.append({"do": "graze", "at": t, "dur": r.uniform(2.0, 3.5), "sfx": False})
                t += r.uniform(4.5, 7.0)
            out.append((layer, dict(base, x=x, face=r.choice(["left", "right"]), actions=acts)))
        elif mode in ("peck", "perch"):
            x = float(L.get("x", r.uniform(0.1, 0.9)))
            acts = [{"do": "peck", "at": t, "dur": 1.2, "sfx": False} for t in [r.uniform(0.5, 1.5) + 3.5 * k for k in range(int(dur / 3.5) + 1)]]
            out.append(("set", dict(base, x=x, face=r.choice(["left", "right"]), actions=acts if mode == "peck" else acts[::2])))
        elif mode == "glide":
            wy = (water[0]["y0"] + 0.025) if water else ground - 0.03
            x0 = r.uniform(0.05, 0.4)
            v = float(L.get("speed", 0.02))
            out.append(("set", dict(base, x=x0, y=wy, face="right",
                                    actions=[{"do": "move", "at": 0, "to": x0 + v * dur, "dur": dur}])))
            out.append(("set", dict(base, x=x0 + 0.5, y=wy + 0.015, face="left", scale=0.85,
                                    actions=[{"do": "move", "at": 0, "to": x0 + 0.5 - v * dur * 0.8, "dur": dur}])))
        elif mode == "fly_across":
            speed = float(L.get("speed", 0.2))
            d = 1.5 / speed
            period = float(L.get("period", 9))
            t0 = r.uniform(0.5, 3.0)
            while t0 < dur:
                go_right = r.random() < 0.5
                x0, x1 = (-0.2, 1.2) if go_right else (1.2, -0.2)
                y = float(L.get("y", r.uniform(0.22, 0.42)))
                out.append(("mid", dict(base, x=x0, y=y, face="right" if go_right else "left",
                                        actions=[{"do": "hidden", "at": 0, "dur": t0},
                                                 {"do": "fly", "at": t0, "to": x1, "dur": d, "height": 0, "arc": False,
                                                  "sfx": False}])))
                t0 += d + period
        elif mode == "circle":
            out.append(("mid", dict(base, x=0.5, y=float(L.get("y", 0.22)),
                                    actions=[{"do": "soar", "at": 0, "dur": dur + 5, "cx": r.uniform(0.35, 0.65),
                                              "rx": r.uniform(0.18, 0.32), "ry": 5.0, "speed": r.uniform(0.18, 0.3),
                                              "phase": r.uniform(0, 6)}])))
        elif mode == "hover":
            y = float(L.get("y", 0.55))
            x0 = r.uniform(0.15, 0.85)
            acts = [{"do": "hover", "at": 0, "dur": dur + 2, "flap": 18 if "butterfly" in L["who"] else 10}]
            t, x = 0.0, x0
            while t < dur:
                nx = min(0.95, max(0.05, x + r.uniform(-0.2, 0.2)))
                acts.append({"do": "move", "at": t, "to": nx, "dur": 2.5, "dy": r.uniform(-4, 4)})
                t += 2.5
                x = nx
            out.append(("set", dict(base, x=x0, y=y, actions=acts)))
        elif mode == "leap":
            period = float(L.get("period", 6))
            wy = float(L.get("y", (water[0]["y0"] + 0.05) if water else ground))
            t0 = r.uniform(0.5, 2.5)
            while t0 < dur:
                go_right = r.random() < 0.5
                out.append(("set", dict(base, x=r.uniform(0.15, 0.85), y=wy, face="right" if go_right else "left",
                                        actions=[{"do": "hidden", "at": 0, "dur": t0},
                                                 {"do": "leap", "at": t0, "dur": 0.9, "height": 12, "dx": 0.06}])))
                t0 += period * r.uniform(0.7, 1.3)
    return out


class Performer:
    def __init__(self, cfg, W, H, ground, zmax=1.15, seed=0):
        self.cfg = cfg
        who = cfg.get("who", cfg.get("id"))
        self.spec = get_entity(who)
        self.kind = self.spec.get("kind", "humanoid")
        self.depth = float(cfg.get("depth", 1.0))
        self.scale = float(cfg.get("scale", 1.0))
        U = stage_unit(W, H)
        need = CHAR_HEIGHT * U * self.scale * max(0.6, self.depth) ** 0.8 * zmax * float(self.spec.get("scale", 1.0))
        if self.kind != "humanoid":
            from .fauna import size_factor
            need *= size_factor(self.spec)
        ppu = _ppu_bucket(need * 1.1)
        if self.kind == "humanoid":
            self.rig = build_character(self.spec, ppu=ppu)
            self.rig.meta.setdefault("ground_seated", 9.4)
        else:
            self.rig = build_creature(self.spec, ppu=ppu)
        self.U, self.W, self.H = U, W, H
        self.ground = ground
        self.x0 = float(cfg.get("x", 0.5))
        self.y = cfg.get("y", "ground")
        f = cfg.get("face", "right")
        self.face0 = 1 if f in ("right", 1, "r") else -1
        self.mode0 = cfg.get("pose", "stand")
        acts = list(cfg.get("actions", []) or [])
        if self.mode0 in ("seated", "sit"):
            self.mode0 = "seated"
        if self.mode0 == "meditate":
            acts.insert(0, {"do": "meditate", "at": 0})
            self.mode0 = "seated"
        acts.sort(key=lambda a: float(a.get("at", 0)))
        self.actions = acts
        self.seed = (hash(str(who)) % 1000) / 97.0 + seed
        self.strings = cfg.get("strings", True)
        self.shadow = cfg.get("shadow_puppet", False)
        self.ambient = cfg.get("ambient", False)
        self.order = float(cfg.get("z", self.depth))

    def head_target(self, t, framing="medium"):
        """(x, y) frame point to centre the camera on for this character."""
        st = A.evaluate(self.rig, self.x0, self.face0, self.mode0, self.actions, t, self.seed)
        gy = self.ground - (1 - self.depth) * 0.12 if self.y == "ground" else float(self.y)
        h = CHAR_HEIGHT * self.U * self.scale * self.depth ** 0.8 * float(self.rig.meta.get("scale", 1.0)) * st.scale
        tall = (self.rig.ground + 52) * h / self.H if self.kind == "humanoid" else self.rig.ground * 2.0 * h / self.H
        if st.mode == "seated":
            tall *= 0.62
        frac = {"wide": 0.45, "full": 0.58, "medium": 0.68, "close": 0.8, "extreme": 0.86}.get(framing, 0.66)
        return st.x, gy + st.dy * h / self.H - tall * frac

    def draw(self, frame, t, cam, light, env_time, sil_k=0.0):
        st = A.evaluate(self.rig, self.x0, self.face0, self.mode0, self.actions, t, self.seed)
        if st.alpha <= 0.01:
            return
        W, H = self.W, self.H
        par = clamp(self.depth, 0.4, 1.5)
        gy = self.ground - (1 - self.depth) * 0.12 if self.y == "ground" else float(self.y)
        sx, sy, ez = to_screen(st.x, gy, cam, par, W, H)
        k = CHAR_HEIGHT * self.U * self.scale * self.depth ** 0.8 * ez * float(self.rig.meta.get("scale", 1.0)) * st.scale
        pose = dict(st.pose)
        pose["_root"] = st.rot
        flip = st.face < 0
        swaps = {}
        if self.kind == "bird" and st.flying and "flying_body" in self.rig.meta:
            swaps["body"] = self.rig.meta["flying_body"]
        canvas, ox, oy, solved = self.rig.render(pose, k, flip=flip, hidden=st.hidden, show=st.show, swaps=swaps)
        ground_off = self.rig.ground
        if st.mode == "seated":
            ground_off = self.rig.meta.get("ground_seated", 9.4)
        root_x = sx + st.dx * k * (-1 if flip else 1)
        root_y = sy - ground_off * k + st.dy * k
        if st.flipx < 0.999:
            w, h = canvas.size
            nw = max(2, int(w * max(0.04, st.flipx)))
            canvas = canvas.resize((nw, h), Image.BILINEAR)
            ox = ox * nw / w
        sil = st.silhouette or self.shadow or sil_k > 0.97
        if 0.02 < sil_k <= 0.97 and not sil:
            a = canvas.getchannel("A")
            dark = Image.new("RGBA", canvas.size, (18, 12, 8, 255))
            canvas = Image.blend(canvas, dark, sil_k)
            canvas.putalpha(a)
        if sil:
            a = canvas.getchannel("A")
            canvas = Image.new("RGBA", canvas.size, (18, 12, 8, 255))
            canvas.putalpha(a.filter(ImageFilter.GaussianBlur(max(0.6, H / 1400))))
        elif self.depth < 0.95:
            fog = clamp((1 - self.depth) * 0.7, 0, 0.6)
            tint = Image.new("RGBA", canvas.size, rgb(light["haze"])[:3] + (255,))
            a = canvas.getchannel("A")
            canvas = Image.blend(canvas, tint, fog)
            canvas.putalpha(a)
        night = light.get("time") in ("night", "cosmic", "fire")
        img = canvas
        if not sil:
            img = pop_light(canvas, light.get("light", "#ffe6a8"), H, glow=st.glow, ambient=self.ambient,
                            night=night, fade=1 - 0.75 * sil_k, depth=self.depth)
        if st.alpha < 0.999:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * st.alpha)))
        x, y = int(round(root_x - ox)), int(round(root_y - oy))
        from .envs import _safe_paste
        _safe_paste(frame, img, x, y)
        # puppet strings to the fly bar (above the frame)
        if self.strings and not self.ambient and not st.flying and st.mode != "lying" and not sil and st.alpha > 0.5:
            pts = []
            for an in ("head", "hand_f", "hand_b"):
                if an in self.rig.anchors and self.rig.anchors[an][0] in solved:
                    ux, uy = self.rig.anchor_world(solved, an)
                    pts.append((root_x + (-ux if flip else ux) * k * max(0.04, st.flipx), root_y + uy * k))
            draw_strings(frame, pts, alpha=int(70 * st.alpha), width=max(1, int(H / 900)), top=-5,
                         sway_px=math.sin(t * 1.25 + self.seed) * H * 0.004)


# =========================================================================== shot runtime

class ShotRuntime:
    def __init__(self, shot, W, H, seed=0):
        self.shot = shot
        self.W, self.H = W, H
        self.env = build_env(shot["env"], W, H, seed=shot.get("env_seed", 0))
        self.dur = float(shot["dur"])
        cam = shot.get("camera", {}) or {}
        zmax = max(cam.get("from", 1.15), cam.get("to", 1.15), 1.15, FRAMES.get(cam.get("frame"), 1.0),
                   1.5 if cam.get("move") in ("push_to", "reveal", "establish") else 1.0)
        self.performers = [Performer(c, W, H, self.env.ground, zmax, seed=i) for i, c in enumerate(shot.get("cast", []))]
        self.performers.sort(key=lambda p: p.order)
        self.by_id = {p.cfg.get("id", p.cfg.get("who")): p for p in self.performers}
        # ambient background life (deer, swans, birds, soldiers ...) — storyboard `life:` adds/overrides, false disables
        life = [] if shot.get("life") is False else list(self.env.life) + list(shot.get("life") or [])
        self.life = {"mid": [], "set": []}
        for layer, c in life_casts(life, self.dur + 3.0, self.env.ground, self.env.water, seed=f"{shot.get('id')}"):
            try:
                self.life[layer].append(Performer(c, W, H, self.env.ground, 1.15, seed=len(self.life[layer])))
            except KeyError:
                pass
        for k in self.life:
            self.life[k].sort(key=lambda p: p.depth)
        L = dict(self.env.light)
        L.update(shot.get("light", {}) or {})
        self.light = L
        self.tex = light_textures(W, H, tuple(L.get("spot", (0.5, 0.42))), L.get("spot_color", L["light"]),
                                  float(L.get("vignette", 0.6)), float(L.get("amb", 1.0)), L.get("haze", "#e8d8b4"))
        self.waves = wave_layers(self.env, W, H)
        # extra props from the storyboard
        U = stage_unit(W, H)
        self.extra_hanging = []
        self.extra_layers = {}
        for pr in shot.get("props", []) or []:
            pr = dict(pr)
            name = pr.pop("name")
            x, y = float(pr.pop("x", 0.5)), pr.pop("y", None)
            s = float(pr.pop("s", pr.pop("scale", 1.0)))
            layer = pr.pop("layer", "ground")
            hang = pr.pop("hang", name in ("cloud", "sun", "moon", "star"))
            flip = pr.pop("flip", False)
            spr = build_prop(name, U * s, **pr)
            if hang:
                self.extra_hanging.append(dict(sprite=spr, x=x, y=float(y if y is not None else 0.15), phase=x * 7,
                                               parallax=0.85, amp=1.8))
            else:
                yy = float(y) if y is not None else self.env.ground + (0.04 if layer == "ground" else -0.02)
                self.extra_layers.setdefault(layer, []).append((spr.flipped() if flip else spr, x, yy))
        fx = shot.get("fx", []) or []
        self.fx_static = set()
        self.fx_events = []
        for f in fx:
            if isinstance(f, str) and "@" in f:
                n, at = f.split("@", 1)
                self.fx_events.append((n.strip(), float(at)))
            elif isinstance(f, dict):
                self.fx_events.append((f.get("name"), float(f.get("at", 0))))
            else:
                self.fx_static.add(f)
        self.particles = [p for p in ("dust", "embers", "fireflies", "petals", "snow", "rain", "stars") if p in self.fx_static]
        if not self.particles and self.light.get("particles") and "no_particles" not in self.fx_static:
            self.particles = [self.light["particles"]]
        self.rays_k = float(self.light.get("rays", 0.3)) + (0.5 if "rays" in self.fx_static else 0)
        self.seed = seed
        t_ = self.light.get("time")
        default_grade = {"night": "kathaa_night", "fire": "agni", "dusk": "rakt", "divine": "swarna", "cosmic": "neel",
                         "storm": "neel", "dawn": "prabhat"}.get(t_, "kathaa")
        self.grade = shot.get("grade") or default_grade
        dim_default = {"night": 0.78, "cosmic": 0.8, "fire": 0.8, "dusk": 0.8, "storm": 0.78}.get(t_, 0.82)
        self.bg_dim = float(self.light.get("bg_dim", dim_default))
        self.bg_desat = float(self.light.get("bg_desat", 0.8))

    # ------------------------------------------------------------------
    def camera(self, t, cam_dx=0.0):
        cam = self.shot.get("camera", {}) or {}
        target = None
        on = cam.get("on") or cam.get(True) or cam.get("target") or (cam.get("follow") if isinstance(cam.get("follow"), str) else None)
        if on and on in self.by_id:
            perf = self.by_id[on]
            lag = 0.35 if cam.get("move") == "follow" else 0.0
            framing = cam.get("frame", "medium")
            target = lambda tt, p=perf, f=framing, lg=lag: p.head_target(max(0.0, tt - lg), f)
        x, y, z = camera_at(cam, t, self.dur, target)
        x += cam_dx
        sh = float(cam.get("shake", 0.0))
        for n, at in self.fx_events:
            if n in ("shake", "quake") and 0 <= t - at < 0.8:
                sh = max(sh, 1.0 * (1 - (t - at) / 0.8))
        if sh > 0:
            x += sh * 0.006 * math.sin(t * 57)
            y += sh * 0.006 * math.cos(t * 43)
            z = max(z, 1.02)
        return clamp_cam(x, y, z)

    def dim_level(self, t):
        """0 = normal light, 1 = stage lights down (puppets become silhouettes against the backdrop)."""
        lvl = 0.0
        for n, at in sorted(self.fx_events, key=lambda e: e[1]):
            if n in ("dim", "silhouettes", "lights_down") and t >= at:
                lvl = max(lvl, smooth((t - at) / 1.2))
            elif n in ("lights_up", "undim") and t >= at:
                lvl = min(lvl, 1 - smooth((t - at) / 1.2))
        return lvl

    def _anim(self, frame, layer, order, t, cam):
        """Wind-animated env props: traveling gusts make trees, grass & flowers sway in a wave."""
        W, H = self.W, self.H
        par = LAYER_PAR.get(layer, 1.0)
        gust = 0.65 + 0.35 * math.sin(0.23 * t) + 0.15 * math.sin(0.71 * t + 1.0)
        for a in self.env.anim:
            if a["layer"] != layer or a["order"] != order:
                continue
            sx, sy, ez = to_screen(a["x"], a["y"], cam, par, W, H)
            if sx < -W * 0.5 or sx > W * 1.5:
                continue
            ph = a["phase"] - a["x"] * 4.0
            w = 2 * math.pi * a["freq"] * 0.5
            kind = a["kind"]
            if kind.startswith("sway"):
                ang = a["amp"] * gust * (math.sin(w * t + ph) + 0.35 * math.sin(2.7 * w * t + ph * 1.7))
                affine_paste(frame, a["sprite"], sx, sy, ang, ez, ez)
            elif kind == "bob":
                affine_paste(frame, a["sprite"], sx, sy + a["amp"] * H * math.sin(w * t + ph), 0.8 * math.sin(w * t + ph + 1), ez, ez)
            elif kind == "flutter":
                kx = 1 - a["amp"] * (0.5 + 0.5 * math.sin(3.2 * w * t + ph))
                affine_paste(frame, a["sprite"], sx, sy, 0.6 * math.sin(w * t + ph), ez * kx, ez)
            else:
                affine_paste(frame, a["sprite"], sx, sy, 0, ez, ez)

    def _drift(self, frame, t, cam):
        W, H = self.W, self.H
        for d in self.env.drift:
            x = ((d["x"] + d["speed"] * t + 0.35) % 1.7) - 0.35
            sx, sy, ez = to_screen(x, d["y"] + 0.006 * math.sin(t * 0.4 + d["x"] * 5), cam, d.get("parallax", 0.2), W, H)
            spr = d["sprite"]
            if d.get("curl") and d["speed"] < 0:
                spr = spr.flipped()
            affine_paste(frame, spr, sx, sy, 2.0 * math.sin(t * 0.6 + d["x"]) if d.get("curl") else 0, ez, ez)

    def _life(self, frame, layer, t, cam, sil_k):
        for p in self.life.get(layer, []):
            p.draw(frame, t, cam, self.light, t, sil_k * 0.6)

    def _hanging(self, frame, items, t, cam):
        W, H = self.W, self.H
        for h in items:
            spr = h["sprite"]
            par = h.get("parallax", 0.85)
            hx, hy, ez = to_screen(h["x"], h["y"], cam, par, W, H)
            topx, _, _ = to_screen(h["x"], -0.2, cam, par, W, H)
            ang = h.get("amp", 2.0) * math.sin(t * 0.8 + h["phase"]) * (1 if h.get("string", 1) else 0.4)
            L = hy + H * 0.05
            px = topx - math.sin(math.radians(ang)) * L * 0.2
            affine_paste(frame, spr, px, hy, ang * 0.6, ez, ez)
            if h.get("string", 1) != 0:
                top_y = hy - spr.py * ez
                ImageDraw.Draw(frame).line([(topx, -4), (px, top_y + spr.py * ez * 0.3)], fill=(236, 226, 200, 110),
                                           width=max(1, int(H / 900)))

    def _flames(self, frame, t, cam):
        W, H = self.W, self.H
        for fl in self.env.flames:
            sx, sy, ez = to_screen(fl["x"], fl["y"], cam, fl.get("parallax", 1.0), W, H)
            size = int(max(6, fl["size"] * self.H * 0.022 * ez))
            frames = flame_frames(min(400, size - size % 2), fl.get("kind", "lamp"))
            idx = int(t * 10 + fl["phase"] * 3) % len(frames)
            spr = frames[idx]
            # warm light pool
            glow = soft_dot(int(size * 2.2), "#ffb050", 110)
            frame.alpha_composite(glow, (int(sx - glow.size[0] / 2), int(sy - glow.size[1] * 0.62)))
            affine_paste(frame, spr, sx, sy, 0, 1.0, 1.0 + 0.06 * math.sin(t * 13 + fl["phase"]))

    def frame(self, t, cam_dx=0.0) -> Image.Image:
        W, H = self.W, self.H
        cam = self.camera(t, cam_dx)
        sil_k = self.dim_level(t)
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        drawn_perf = False
        for name, par, img in self.env.layers:
            if name == "front" and not drawn_perf:
                frame = self._dim_set(frame)
                self._flames(frame, t, cam)
                self._actors(frame, t, cam, sil_k)
                for spr, x, y in self.extra_layers.get("over", []):
                    sx, sy, ez = to_screen(x, y, cam, 1.0, W, H)
                    affine_paste(frame, spr, sx, sy, 0, ez, ez)
                drawn_perf = True
            self._anim(frame, name, "under", t, cam)
            if img is not None:
                frame.alpha_composite(layer_view(img, cam, par, W, H))
            self._anim(frame, name, "over", t, cam)
            if name == "sky":
                self._drift(frame, t, cam)
                draw_birds(frame, self.env.birds, t, W, H, seed=self.seed,
                           color="#2a1c14" if self.light.get("time") not in ("night", "cosmic") else "#0a0a14")
            if name == "mid":
                self._life(frame, "mid", t, cam, sil_k)
            if name == "set":
                if self.waves:
                    wl, wp = self.waves[int(t * 4) % len(self.waves)]
                    frame.alpha_composite(layer_view(wl, cam, wp, W, H))
                self._life(frame, "set", t, cam, sil_k)
                self._hanging(frame, self.env.hanging + self.extra_hanging, t, cam)
            if name == "ground":
                for spr, x, y in self.extra_layers.get("ground", []):
                    sx, sy, ez = to_screen(x, y, cam, 1.0, W, H)
                    affine_paste(frame, spr, sx, sy, 0, ez, ez)
        if not drawn_perf:
            frame = self._dim_set(frame)
            self._flames(frame, t, cam)
            self._actors(frame, t, cam, sil_k)
            for spr, x, y in self.extra_layers.get("over", []):
                sx, sy, ez = to_screen(x, y, cam, 1.0, W, H)
                affine_paste(frame, spr, sx, sy, 0, ez, ez)
        for spr, x, y in self.extra_layers.get("front", []):
            sx, sy, ez = to_screen(x, y, cam, 1.3, W, H)
            affine_paste(frame, spr, sx, sy, 0, ez, ez)
        return self._light(frame, t, sil_k)

    def _dim_set(self, frame):
        """Push the set back: dimmer, less saturated and softer than the lit puppets (reference look)."""
        k = self.bg_dim
        if k >= 0.995 and self.bg_desat >= 0.995:
            return frame
        from PIL import ImageEnhance
        rgbf = frame.convert("RGB")
        if self.bg_desat < 0.995:
            rgbf = ImageEnhance.Color(rgbf).enhance(self.bg_desat)
        if k < 0.995:
            rgbf = Image.eval(rgbf, lambda v, kk=k: int(v * kk))
        return rgbf.convert("RGBA")

    def _actors(self, frame, t, cam, sil_k=0.0):
        for p in self.performers:
            p.draw(frame, t, cam, self.light, t, sil_k)

    def _light(self, frame, t, sil_k=0.0):
        W, H = self.W, self.H
        spot, vig, haze, rays = self.tex
        rgbf = frame.convert("RGB")
        if sil_k > 0.01:   # house lights down: backdrop glows on, scene dims
            rgbf = Image.eval(rgbf, lambda v, kk=sil_k: int(v * (1 - 0.22 * kk)))
        # warm stage spot (screen)
        rgbf = ImageChops.screen(rgbf, Image.eval(spot, lambda v: int(v * 0.30)))
        if self.rays_k > 0.01:
            k = 0.5 + 0.5 * math.sin(t * 0.35)
            rr = Image.blend(rays[0], rays[1], k)
            rgbf = ImageChops.screen(rgbf, Image.eval(rr, lambda v, kk=self.rays_k: int(v * min(1.0, kk * 0.8))))
        # drifting smoky haze
        off = int((t * W * 0.012) % W)
        hz = haze.crop((off, 0, off + W, H))
        hk = float(self.light.get("haze_k", 0.2 if self.light.get("time") not in ("night", "cosmic") else 0.12))
        rgbf = ImageChops.screen(rgbf, Image.eval(hz, lambda v: int(v * hk)))
        out = rgbf.convert("RGBA")
        for p in self.particles:
            draw_particles(out, p, t, W, H, 1.4 if p == "dust" and self.light.get("dust") else 1.0, seed=self.seed)
        rgbf = out.convert("RGB")
        rgbf = ImageChops.multiply(rgbf, vig)
        rgbf = apply_grade(rgbf, self.grade)
        # timed fx
        for n, at in self.fx_events:
            lt = t - at
            if n == "flash" and 0 <= lt < 0.5:
                rgbf = Image.blend(rgbf, Image.new("RGB", (W, H), (255, 246, 220)), 0.85 * (1 - lt / 0.5))
            elif n == "lightning" and 0 <= lt < 0.6:
                a = 0.8 if (lt < 0.08 or 0.18 < lt < 0.26) else 0.0
                if a:
                    rgbf = Image.blend(rgbf, Image.new("RGB", (W, H), (225, 235, 255)), a)
            elif n in ("divine_burst", "burst") and 0 <= lt < 1.6:
                k = lt / 1.6
                g = radial(W // 4, H // 4, W // 8, H // 9, (0.2 + k) * W / 4, "#fff2c0", "#fff2c000", 1.5).convert("RGB")
                g = g.resize((W, H), Image.BILINEAR)
                rgbf = ImageChops.screen(rgbf, Image.eval(g, lambda v, kk=k: int(v * (1 - kk) * 0.9)))
            elif n == "fade_in" and lt >= 0:
                d = 1.0
                if lt < d:
                    rgbf = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), rgbf, smooth(lt / d))
            elif n == "fade_out":
                d = 1.0
                if lt > 0:
                    rgbf = Image.blend(rgbf, Image.new("RGB", (W, H), (0, 0, 0)), smooth(min(1, lt / d)))
        return rgbf


# =========================================================================== timeline & chunked encode

class Timeline:
    def __init__(self, plan):
        self.plan = plan
        self.W, self.H, self.fps = plan["W"], plan["H"], plan["fps"]
        self.shots = plan["shots"]
        self.pre = float(plan.get("intro", {}).get("pre", 0.0)) if plan.get("intro", {}).get("curtain") else 0.0
        self.post = float(plan.get("outro", {}).get("post", 0.0)) if plan.get("outro", {}).get("curtain") else 0.0
        self.total = self.pre + sum(float(s["dur"]) for s in self.shots) + self.post
        self.nframes = int(math.ceil(self.total * self.fps))
        self._rt = {}
        self._curtain = None

    def runtime(self, i):
        if i not in self._rt:
            if len(self._rt) > 3:
                self._rt.pop(next(iter(self._rt)))
            self._rt[i] = ShotRuntime(self.shots[i], self.W, self.H, seed=i)
        return self._rt[i]

    def locate(self, T):
        t = T - self.pre
        if t < 0:
            return 0, 0.0
        for i, s in enumerate(self.shots):
            d = float(s["dur"])
            if t < d or i == len(self.shots) - 1:
                return i, t
            t -= d
        return len(self.shots) - 1, t

    def _wipe(self, i, t, td, tr):
        """Foreground wipe: a big dark element sweeps past the lens (camera trucking right) and
        hides the change of set — the reference's signature scene transition."""
        W, H = self.W, self.H
        k = clamp(t / td)
        prev = self.runtime(i - 1)
        cur = self.runtime(i)
        if tr == "wipe":
            env = self.shots[i]["env"]
            tr = next((v for kk, v in WIPE_BY_LOCALE.items() if env.startswith(kk)), "wipe_tree")
        kb = smooth(clamp((k - 0.32) / 0.36))
        a = prev.frame(float(self.shots[i - 1]["dur"]) + t, cam_dx=0.05 * k) if kb < 0.999 else None
        b = cur.frame(t, cam_dx=-0.05 * (1 - k)) if kb > 0.001 else None
        base = a if b is None else (b if a is None else Image.blend(a, b, kb))
        out = base.convert("RGBA")
        e = ease_in_out(k)
        for spr, off, ys in wipe_sprites(tr, H):
            x = W * (1.45 - 1.9 * e + off)
            affine_paste(out, spr, x, H * ys, 0, 1.0, 1.0)
        return out.convert("RGB")

    def render(self, fi) -> Image.Image:
        T = fi / self.fps
        i, t = self.locate(T)
        img = self.runtime(i).frame(t)
        # transition into this shot from the previous one
        s = self.shots[i]
        tr = s.get("transition", "crossfade")
        td = float(s.get("trans_dur", (1.3 if str(tr).startswith("wipe") else 0.6) if tr != "cut" else 0))
        if i > 0 and tr != "cut" and t < td:
            prev = self.runtime(i - 1)
            k = smooth(t / td)
            if tr == "crossfade":
                pimg = prev.frame(float(self.shots[i - 1]["dur"]) + t)
                img = Image.blend(pimg, img, k)
            elif tr in ("dip", "dip_black"):
                if k < 0.5:
                    pimg = prev.frame(float(self.shots[i - 1]["dur"]) + t)
                    img = Image.blend(pimg, Image.new("RGB", img.size, (0, 0, 0)), k * 2)
                else:
                    img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, (k - 0.5) * 2)
            elif tr == "flash":
                img = Image.blend(img, Image.new("RGB", img.size, (255, 246, 222)), (1 - k) * 0.9)
            elif tr.startswith("wipe"):
                img = self._wipe(i, t, td, tr)
        # curtain
        intro, outro = self.plan.get("intro", {}), self.plan.get("outro", {})
        if intro.get("curtain") or outro.get("curtain"):
            from .curtain import Curtain
            if self._curtain is None:
                self._curtain = Curtain(self.W, self.H)
            open_dur = float(intro.get("open", 2.4))
            close_dur = float(outro.get("close", 2.0))
            end_shots = self.pre + sum(float(x["dur"]) for x in self.shots)
            k_open = None
            if intro.get("curtain") and T < self.pre + open_dur:
                k_open = 0.0 if T < self.pre else smooth((T - self.pre) / open_dur)
            if outro.get("curtain") and T >= end_shots:
                k_open = 1.0 - smooth((T - end_shots) / close_dur)
            if k_open is not None and k_open < 0.999:
                img = self._curtain.overlay(img, k_open, T)
        return img


WIPE_BY_LOCALE = {"forest": "wipe_leaf", "palace_garden": "wipe_leaf", "vrindavan": "wipe_leaf", "ashram": "wipe_leaf",
                  "village": "wipe_leaf", "lotus": "wipe_leaf", "palace": "wipe_pillar", "temple": "wipe_pillar",
                  "yagya": "wipe_pillar", "dwarka": "wipe_pillar", "patala": "wipe_pillar", "lanka": "wipe_pillar",
                  "swarga": "wipe_cloud", "kshirsagar": "wipe_cloud", "cosmic": "wipe_cloud", "kailash": "wipe_cloud"}


@lru_cache(maxsize=8)
def wipe_sprites(kind, H):
    """Foreground elements for wipes — pre-silhouetted and soft-focused (they are right at the lens)."""
    U = H / 100.0
    if kind == "wipe_pillar":
        sp = build_prop("fg_pillar", U * 1.1, h=120)
        items = [(sp, 0.0, 1.06), (sp, 0.42, 1.06)]
    elif kind == "wipe_cloud":
        c = build_prop("cloud", U * 4.2, color="#f3e9d2", kind="puffy", seed=3)
        items = [(c, 0.0, 0.62), (c, 0.36, 0.86), (c, -0.3, 0.4)]
    elif kind == "wipe_tree":
        tr = build_prop("tree", U * 1.6, kind="night", h=70, seed=5, night=True)
        items = [(tr, 0.0, 1.12), (build_prop("leaf_cluster", U * 1.5, seed=2), 0.3, 1.1)]
    else:
        lc = build_prop("leaf_cluster", U * 1.9, seed=1)
        lc2 = build_prop("leaf_cluster", U * 1.6, seed=4)
        items = [(lc, 0.0, 1.18), (lc2, 0.33, 0.95), (lc, -0.28, 0.72)]
    out = []
    for spr, off, ys in items:
        if kind != "wipe_cloud":
            spr = spr.silhouette("#120c08")
        pad = int(H / 60)
        im = Image.new("RGBA", (spr.img.width + 2 * pad, spr.img.height + 2 * pad), (0, 0, 0, 0))
        im.alpha_composite(spr.img, (pad, pad))
        im = im.filter(ImageFilter.GaussianBlur(H / 200))
        out.append((Sprite(im, spr.px + pad, spr.py + pad), off, ys))
    return out


def _encode_chunk(args):
    plan, f0, f1, out, crf, preset = args
    tl = Timeline(plan)
    W, H, fps = tl.W, tl.H, tl.fps
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(f0, f1):
        img = tl.render(fi)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for chunk {out}")
    return out, f1 - f0, time.time() - t0


def warm_assets(plan):
    """Build every rig/env once in this process so worker processes hit the disk cache."""
    W, H = plan["W"], plan["H"]
    for i, s in enumerate(plan["shots"]):
        ShotRuntime(s, W, H, seed=i)


def render_video(plan, out_path, workers=None, chunk=48, crf=16, preset="veryfast", log=print):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tl = Timeline(plan)
    n = tl.nframes
    workers = workers or max(1, (os.cpu_count() or 2))
    log(f"[render] {n} frames @ {tl.fps}fps  {tl.W}x{tl.H}  ({tl.total:.1f}s)  workers={workers}")
    t0 = time.time()
    warm_assets(plan)
    log(f"[render] assets ready in {time.time() - t0:.1f}s")
    tmp = Path(tempfile.mkdtemp(prefix="mythic_chunks_", dir=str(out_path.parent)))
    jobs = []
    for k, f0 in enumerate(range(0, n, chunk)):
        jobs.append((plan, f0, min(n, f0 + chunk), str(tmp / f"c{k:05d}.mp4"), crf, preset))
    done = 0
    t1 = time.time()
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for out, cnt, dt in ex.map(_encode_chunk, jobs):
                done += cnt
                el = time.time() - t1
                log(f"[render] {done}/{n} frames  {done / max(0.01, el):.1f} fps  eta {el / max(1, done) * (n - done):.0f}s")
    else:
        for j in jobs:
            out, cnt, dt = _encode_chunk(j)
            done += cnt
            log(f"[render] {done}/{n} frames  {cnt / max(0.01, dt):.1f} fps")
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{j[3]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(out_path)], check=True)
    for j in jobs:
        try:
            os.remove(j[3])
        except OSError:
            pass
    try:
        lst.unlink()
        tmp.rmdir()
    except OSError:
        pass
    log(f"[render] wrote {out_path}  in {time.time() - t0:.1f}s")
    return out_path


def render_still(plan, T, out_png):
    tl = Timeline(plan)
    img = tl.render(int(T * tl.fps))
    img.save(out_png)
    return out_png
