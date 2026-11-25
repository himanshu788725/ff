"""2.5D environments: locale x time-of-day presets composed into parallax layers.

An environment id is "<locale>_<time>" (e.g. kurukshetra_dusk, ashram_dawn,
lanka_fire).  `list_envs()` gives all 100+ ids.  `build_env(id, W, H)` returns
an `Env` with static layer images plus animated elements (hanging props,
flames, water, birds) and the lighting recipe used by the renderer.
"""
from __future__ import annotations

import math
import pickle
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFilter

from .gfx import linear_gradient, paper, radial, Sprite, noise
from .props import HANGING, build_prop
from .util import code_version, CACHE_DIR, mix, rgb, rng, shade, stable_hash

ENV_VERSION = code_version("envs", "props", "gfx")
M = 0.16          # overscan margin (fraction of frame) on every side of a layer
GROUND = 0.845    # default ground line (feet) as fraction of frame height

LAYERS = [("sky", 0.08), ("far", 0.28), ("mid", 0.55), ("set", 0.82), ("ground", 1.0), ("front", 1.3)]

TIMES = {
    "dawn":   dict(sky=[(0, "#6e5a72"), (0.55, "#c98f7e"), (1, "#efc493")], haze="#f2cfa4", light="#ffdcaa", amb=0.92,
                   celestial="sun_low", far="#7a6476", vign=0.62, rays=0.35, particles="dust", ground_k=-0.02),
    "day":    dict(sky=[(0, "#7a6c76"), (0.55, "#c2ae98"), (1, "#e2cfa8")], haze="#efe0bc", light="#fff1cc", amb=0.97,
                   celestial="sun", far="#8f7f86", vign=0.62, rays=0.3, particles="dust", ground_k=0.0),
    "dusk":   dict(sky=[(0, "#3c2424"), (0.5, "#9a4434"), (1, "#e08e56")], haze="#e39a62", light="#ffb27a", amb=0.84,
                   celestial="sun_low", far="#5a3434", vign=0.7, rays=0.4, particles="dust", ground_k=-0.08),
    "night":  dict(sky=[(0, "#120b0a"), (0.6, "#2a1a17"), (1, "#3e2a24")], haze="#6a4c3e", light="#ffd8a0", amb=0.66,
                   celestial="moon", far="#2a1c1a", vign=0.8, rays=0.0, particles="fireflies", ground_k=-0.32, stars=True),
    "fire":   dict(sky=[(0, "#140806"), (0.5, "#5a180e"), (1, "#c8461e")], haze="#ff7a2a", light="#ffa050", amb=0.74,
                   celestial=None, far="#3a1410", vign=0.78, rays=0.15, particles="embers", ground_k=-0.18),
    "divine": dict(sky=[(0, "#b88a44"), (0.6, "#eccb86"), (1, "#fff0c6")], haze="#fff0c4", light="#fff4d0", amb=1.05,
                   celestial="sun", far="#c8a878", vign=0.5, rays=0.75, particles="petals", ground_k=0.05),
    "storm":  dict(sky=[(0, "#1e2228"), (0.6, "#4a5058"), (1, "#7a7c78")], haze="#8a9090", light="#d8e0e8", amb=0.7,
                   celestial=None, far="#3a3e44", vign=0.75, rays=0.0, particles="rain", ground_k=-0.2),
    "cosmic": dict(sky=[(0, "#07061a"), (0.5, "#1c1446"), (1, "#3a1e52")], haze="#7a5ac8", light="#e0d0ff", amb=0.8,
                   celestial=None, far="#2a1e48", vign=0.7, rays=0.2, particles="stars", ground_k=-0.3, stars=True),
    "snow":   dict(sky=[(0, "#7a8a9a"), (0.6, "#c8d0d4"), (1, "#eef0ec")], haze="#e8eef0", light="#f4f8ff", amb=0.98,
                   celestial="sun", far="#9aa8b4", vign=0.52, rays=0.25, particles="snow", ground_k=0.05),
}


def stage_unit(W, H):
    """Pixels per stage unit (1u = 1% of a 16:9 frame height; portrait frames use width)."""
    return min(H, W * 1.15) / 100.0


def ground_line(W, H):
    return GROUND if W >= H else 0.74


@dataclass
class Env:
    id: str
    W: int
    H: int
    layers: list                     # [(name, parallax, Image)]
    hanging: list = field(default_factory=list)   # dicts: sprite, x, y, string, phase, parallax
    flames: list = field(default_factory=list)    # dicts: x, y, size, parallax, kind
    water: list = field(default_factory=list)     # dicts: y0, y1, color, parallax
    birds: int = 0
    light: dict = field(default_factory=dict)
    ground: float = GROUND
    stage_floor: str = "earth"
    anim: list = field(default_factory=list)      # animated props: sprite, layer, x, y, kind, amp, freq, phase, order
    life: list = field(default_factory=list)      # ambient background creatures (deer running, swans gliding ...)
    drift: list = field(default_factory=list)     # sky clouds drifting across


# =========================================================================== layer canvas

class LayerCanvas:
    def __init__(self, W, H, name, parallax):
        self.W, self.H = W, H
        self.LW, self.LH = int(W * (1 + 2 * M)), int(H * (1 + 2 * M))
        self.img = Image.new("RGBA", (self.LW, self.LH), (0, 0, 0, 0))
        self.name, self.parallax = name, parallax

    def xy(self, x, y):
        return (x + M) * self.W, (y + M) * self.H

    def put(self, spr: Sprite, x, y, fog=0.0, fog_color="#e8d8b4", dark=0.0, flip=False):
        if fog > 0:
            spr = spr.tinted(fog_color, fog)
        if dark > 0:
            spr = spr.tinted("#140c08", dark)
        if flip:
            spr = spr.flipped()
        X, Y = self.xy(x, y)
        self.img.alpha_composite(spr.img, (int(X - spr.px), int(Y - spr.py))) if (
            X - spr.px >= 0 and Y - spr.py >= 0) else _safe_paste(self.img, spr.img, int(X - spr.px), int(Y - spr.py))


def _safe_paste(dst, src, x, y):
    w, h = src.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, dst.size[0] - x), min(h, dst.size[1] - y)
    if sx1 > sx0 and sy1 > sy0:
        dst.alpha_composite(src.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))


# =========================================================================== builder context

class B:
    """Helper passed to locale builders."""

    def __init__(self, W, H, T, seed):
        self.W, self.H, self.T = W, H, T
        self.r = rng("env", seed)
        self.ppu = stage_unit(W, H)
        self.L = {n: LayerCanvas(W, H, n, p) for n, p in LAYERS}
        self.hanging, self.flames, self.water = [], [], []
        self.birds = 0
        self.floor = "earth"
        self.floor_color = "#8a6a4a"
        self.ground = ground_line(W, H)
        self.light_over = {}
        self.anim, self.life, self.drift = [], [], []

    AUTO_ANIM = {"tree": "sway", "bush": "sway_fast", "grass": "sway_fast", "flowers": "sway_fast", "reeds": "sway_fast",
                 "lotus": "bob", "flagpole": "flutter", "leaf_cluster": "sway", "chhatra": "sway"}

    def prop(self, layer, name, x, y=None, s=1.0, fog=None, dark=0.0, flip=False, anim="auto", **params):
        """Place a prop. Trees/grass/flowers/flags/lotus are kept as separate animated sprites
        (they sway in the wind); everything else is baked into the layer."""
        y = self.ground if y is None else y
        spr = build_prop(name, self.ppu * s, **params)
        fogd = {"sky": 0.0, "far": 0.42, "mid": 0.2, "set": 0.06, "ground": 0.0, "front": 0.0}
        f = fogd.get(layer, 0) if fog is None else fog
        kind = self.AUTO_ANIM.get(name) if anim == "auto" else anim
        if kind:
            if f > 0:
                spr = spr.tinted(self.T["haze"], f)
            if dark > 0:
                spr = spr.tinted("#140c08", dark)
            if flip:
                spr = spr.flipped()
            if layer in ("far", "front"):
                rad = max(1, self.H / 900) if layer == "far" else max(2, self.H / 280)
                spr = Sprite(spr.img.filter(ImageFilter.GaussianBlur(rad)), spr.px, spr.py)
            depth_amp = {"sky": 0.3, "far": 0.35, "mid": 0.65, "set": 1.0, "ground": 1.0, "front": 1.5}.get(layer, 1.0)
            base_amp = {"sway": 1.1, "sway_fast": 3.2, "bob": 0.0035, "flutter": 0.12}.get(kind, 1.0)
            self.anim.append(dict(sprite=spr, layer=layer, x=x, y=y, kind=kind,
                                  amp=base_amp * (depth_amp if kind.startswith("sway") else 1.0) * self.r.uniform(0.75, 1.25),
                                  freq=self.r.uniform(0.45, 0.75) * (2.2 if kind in ("sway_fast", "flutter") else 1.0),
                                  phase=self.r.uniform(0, 6.28),
                                  order="under" if layer in ("far", "mid", "set") else "over"))
            return spr
        self.L[layer].put(spr, x, y, fog=f, fog_color=self.T["haze"], dark=dark, flip=flip)
        return spr

    def creature(self, who, mode="graze", depth=0.7, **kw):
        """Ambient background life: modes run_across walk_across graze glide fly_across hover leap perch."""
        self.life.append(dict(who=who, mode=mode, depth=depth, **kw))

    def flora(self, density=1.0):
        """Scatter swaying grass tufts & wild flowers along the stage floor + dark foreground clumps."""
        kinds = ["grass", "grass", "flowers", "grass", "flowers", "reeds"] if self.floor in ("grass", "earth") else ["grass"]
        n = int(9 * density)
        for k in range(n):
            x = -0.08 + (k + self.r.uniform(0.1, 0.9)) * 1.16 / n
            y = self.ground + self.r.uniform(0.012, 0.11)
            nm = self.r.choice(kinds)
            params = {"seed": k}
            if nm == "flowers":
                params["color"] = self.r.choice(["vermilion", "#e98aa0", "#f2c94a", "#f6efdf", "saffron"])
            if nm == "grass" and self.floor == "sand":
                params["color"] = "#8a8a44"
            self.prop("ground", nm, x, y, s=self.r.uniform(0.7, 1.2), **params)
        for side in (-0.04, 1.04):
            if self.r.random() < 0.8:
                self.prop("front", "grass", side + self.r.uniform(-0.03, 0.03), 1.02, s=self.r.uniform(2.6, 3.4), dark=0.55,
                          seed=int(side * 10) + 3)

    def drift_cloud(self, n=2, wind=False):
        col = {"night": "#3a3e58", "fire": "#4a2018", "storm": "#4a4e54", "dusk": "#b8705a", "dawn": "#d8b0a4",
               "cosmic": "#3a2e6a", "divine": "#f8eed6"}.get(self.T.get("_name"), "#e8dcc4")
        for i in range(n):
            spr = build_prop("cloud", self.ppu * self.r.uniform(0.7, 1.1), color=col, kind="puffy", seed=40 + i)
            spr = spr.tinted(self.T["haze"], 0.35).with_alpha(0.8)
            self.drift.append(dict(sprite=spr, x=self.r.uniform(-0.1, 1.1), y=self.r.uniform(0.06, 0.24),
                                   speed=self.r.uniform(0.004, 0.009) * self.r.choice((-1, 1)), parallax=0.2))
        if wind:
            spr = build_prop("cloud", self.ppu * 1.0, color="#efe6d0", kind="curl", seed=7)
            self.drift.append(dict(sprite=spr, x=self.r.uniform(0, 1), y=self.r.uniform(0.15, 0.3), speed=0.045,
                                   parallax=0.6, curl=True))

    def hang(self, name, x, y, s=1.0, string=None, parallax=0.85, **params):
        spr = build_prop(name, self.ppu * s, **params)
        self.hanging.append(dict(sprite=spr, x=x, y=y, string=string if string is not None else y + M,
                                 phase=self.r.uniform(0, 6.28), parallax=parallax, amp=self.r.uniform(1.2, 2.6)))

    def flame(self, x, y, size=1.0, parallax=1.0, kind="lamp"):
        self.flames.append(dict(x=x, y=y, size=size, parallax=parallax, kind=kind, phase=self.r.uniform(0, 6.28)))

    def sky(self):
        T = self.T
        c = self.L["sky"]
        stops = [((pp * self.ground + M) / (1 + 2 * M), col) for pp, col in T["sky"]]
        stops = [(0.0, stops[0][1])] + stops + [(1.0, stops[-1][1])]
        g = linear_gradient(c.LW, c.LH, stops)
        tex = paper(c.LW, c.LH, base="#808080", seed=11, strength=1.0, fibers=False)
        from PIL import ImageChops
        g = ImageChops.overlay(g.convert("RGB"), tex.convert("RGB")).convert("RGBA")
        c.img.alpha_composite(g)
        if T.get("stars"):
            d = ImageDraw.Draw(c.img)
            for _ in range(int(c.LW * c.LH / 2500)):
                x, y = self.r.uniform(0, c.LW), self.r.uniform(0, c.LH * 0.7)
                rr = self.r.choice((1, 1, 1, 2, 2, 3)) * self.H / 1080
                a = self.r.randint(90, 230)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(250, 236, 200, a))

    def floor_band(self, kind="earth", color=None, y=None):
        """Ground plane from the ground line to the bottom of the frame."""
        y = self.ground - 0.02 if y is None else y
        self.floor = kind
        c = self.L["ground"]
        X0, Y0 = 0, int((y + M) * self.H)
        w, h = c.LW, c.LH - Y0
        base = color or {"earth": "#8a6a46", "grass": "#5a7234", "sand": "#c8a46a", "stone": "#8a7e6e",
                         "stage": "#5a3a24", "floor": "#b89a6a", "snow": "#e6eaea", "battle": "#6a4a34",
                         "water": "#3a6a7a", "cosmic": "#1a1236", "dark": "#2a2018"}.get(kind, "#8a6a46")
        base = shade(base, self.T.get("ground_k", 0))
        self.floor_color = base
        band = paper(w, h, base=base, seed=5, strength=1.3)
        d = ImageDraw.Draw(band)
        ink = rgb(shade(base, -0.35))[:3] + (140,)
        if kind in ("stage", "floor"):
            n = 7
            for k in range(1, n):
                yy = int(h * (k / n) ** 1.6)
                d.line([(0, yy), (w, yy)], fill=ink, width=max(1, self.H // 540))
            if kind == "floor":
                for k in range(0, w, int(self.H * 0.12)):
                    d.line([(k, 0), (k - w * 0.1, h)], fill=ink, width=1)
        elif kind in ("earth", "battle", "sand", "grass"):
            for _ in range(int(w * h / 3000)):
                x, yy = self.r.uniform(0, w), self.r.uniform(0, h)
                ln = self.r.uniform(4, 16) * self.H / 1080 * (1 + yy / h)
                d.line([(x, yy), (x + ln, yy)], fill=ink, width=max(1, int(self.H / 700)))
            if kind == "battle":
                for _ in range(26):
                    x, yy = self.r.uniform(0, w), self.r.uniform(0, h)
                    rr = self.r.uniform(10, 40) * self.H / 1080
                    d.ellipse([x - rr * 2, yy - rr * 0.5, x + rr * 2, yy + rr * 0.5],
                              fill=rgb(shade(base, -0.25))[:3] + (120,))
        elif kind == "stone":
            for k in range(0, w, int(self.H * 0.09)):
                for j in range(0, h, int(self.H * 0.045)):
                    d.rectangle([k + (j % 2) * self.H * 0.045, j, k + self.H * 0.09 + (j % 2) * self.H * 0.045,
                                 j + self.H * 0.045], outline=ink, width=1)
        # darker near the horizon line, lighter toward the audience
        grad = linear_gradient(w, h, [(0, "#00000070"), (0.35, "#00000010"), (1, "#00000038")])
        band.alpha_composite(grad)
        c.img.alpha_composite(band, (X0, Y0))
        # rim line
        ImageDraw.Draw(c.img).line([(0, Y0), (c.LW, Y0)], fill=rgb(shade(base, -0.45))[:3] + (200,),
                                   width=max(2, self.H // 360))

    def water_band(self, y0, y1, color="#3f6f7a", parallax=1.0, layer="ground"):
        c = self.L[layer]
        Y0, Y1 = int((y0 + M) * self.H), int((y1 + M) * self.H)
        band = linear_gradient(c.LW, max(2, Y1 - Y0), [(0, shade(color, 0.15)), (1, shade(color, -0.2))])
        c.img.alpha_composite(band, (0, Y0))
        self.water.append(dict(y0=y0, y1=y1, color=color, parallax=parallax))

    def mist(self, layer, y, strength=0.5):
        c = self.L[layer]
        Y = int((y + M) * self.H)
        h = int(self.H * 0.2)
        band = linear_gradient(c.LW, h, [(0, rgb(self.T["haze"], 0)), (0.5, rgb(self.T["haze"], int(180 * strength))),
                                         (1, rgb(self.T["haze"], 0))])
        c.img.alpha_composite(band, (0, max(0, Y - h // 2)))

    def celestial(self, x=0.84, y=0.17):
        cel = self.T.get("celestial")
        if cel == "sun":
            self.hang("sun", x, y, s=1.0)
        elif cel == "sun_low":
            self.hang("sun", x, y + 0.06, s=1.05, color="#e8833a", rays="#c8521f")
        elif cel == "moon":
            self.hang("moon", x, y, s=1.1)
            for k in range(3):
                self.hang("star", self.r.uniform(0.08, 0.92), self.r.uniform(0.06, 0.25), s=self.r.uniform(0.7, 1.2))

    def clouds(self, n=2, color=None, y=0.12):
        col = color or {"night": "#4a4e6a", "fire": "#5a2a20", "storm": "#5a5e64", "dusk": "#c87a62",
                        "dawn": "#dcb4a8", "cosmic": "#4a3a7a"}.get(self.T.get("_name"), "#e6d8bc")
        xs = [0.18, 0.62, 0.4, 0.86][:n]
        for i, x in enumerate(xs):
            self.hang("cloud", x + self.r.uniform(-0.05, 0.05), y + self.r.uniform(-0.04, 0.05), s=self.r.uniform(0.8, 1.1),
                      color=col, kind="puffy" if i % 3 != 2 else "curl", seed=i)


# =========================================================================== locales

def L_palace_court(b: B):
    b.sky()
    t = b.T["_name"]
    wall = {"night": "#3a3a6a", "dusk": "#a8703a", "fire": "#6a2a1a"}.get(t, "#2f3a72" if b.r.random() < 0.5 else "#c89a5a")
    b.prop("set", "palace", 0.5, b.ground - 0.01, s=1.05, wall=wall, window="#2a2440" if wall != "#2f3a72" else "#c8d8c8",
           interior=False, seed=b.r.randint(0, 99), w=150, h=66, bays=5)
    b.floor_band("floor", "#7a5a3a")
    for x in (0.12, 0.38, 0.62, 0.88):
        b.prop("ground", "deepstambh", x, b.ground + 0.02, s=1.1)
        b.flame(x, b.ground + 0.02 - 0.255, 1.0)
    b.prop("ground", "throne", 0.5, b.ground - 0.005, s=1.0)
    b.prop("sky", "toran", 0.5, 0.03, s=1.4, w=150)
    b.light_over = dict(spot=(0.5, 0.45), rays=0.35)


def L_palace_garden(b: B):
    b.sky()
    b.celestial()
    b.clouds(2)
    b.prop("far", "city", 0.5, b.ground - 0.12, s=1.2, w=170, h=36)
    for i, x in enumerate((0.05, 0.3, 0.7, 0.95)):
        b.prop("mid", "tree", x, b.ground - 0.04, s=1.1, kind="ashoka" if i % 2 else "flowering", seed=i, h=58)
    b.water_band(b.ground - 0.04, b.ground + 0.02, "#4a7a7a", layer="set")
    b.prop("set", "lotus", 0.3, b.ground + 0.0, s=0.9, n=3, seed=1)
    b.prop("set", "lotus", 0.75, b.ground + 0.0, s=0.8, n=2, seed=2)
    b.floor_band("grass", "#5a7234")
    b.prop("front", "bush", -0.02, 1.02, s=2.0, flowers="#f2a2b8", seed=3, dark=0.35)
    b.prop("front", "bush", 1.02, 1.04, s=2.2, flowers="#f2a2b8", seed=4, dark=0.35)


def L_forest_banana(b: B):
    b.sky()
    b.celestial(0.86, 0.16)
    b.prop("far", "mountains", 0.5, b.ground - 0.16, s=1.0, color=b.T["far"], w=200, h=26, seed=3)
    for i in range(5):
        x = -0.06 + i * 0.27 + b.r.uniform(-0.04, 0.04)
        b.prop("mid", "tree", x, b.ground - 0.07, s=b.r.uniform(0.8, 1.0), kind="banana", seed=i, h=62)
    b.mist("mid", b.ground - 0.12, 0.5)
    b.prop("mid", "waterfall", 0.86, b.ground - 0.07, s=1.0, h=34)
    for i, x in enumerate((0.02, 0.5, 0.97)):
        b.prop("set", "tree", x + b.r.uniform(-0.03, 0.03), b.ground - 0.015, s=b.r.uniform(1.0, 1.2), kind="banana",
               seed=10 + i, h=58)
    b.water_band(b.ground - 0.035, b.ground - 0.01, "#4a7a7a", layer="set")
    b.floor_band("earth", "#6a5a3a")
    b.prop("ground", "lotus", 0.62, b.ground + 0.06, s=0.8, n=2, seed=5)
    b.prop("ground", "rock", 0.85, b.ground + 0.05, s=1.4, seed=2)
    b.prop("front", "tree", -0.08, 1.12, s=1.5, kind="banana", seed=21, dark=0.55, h=70)
    b.prop("front", "tree", 1.08, 1.12, s=1.4, kind="banana", seed=22, dark=0.55, h=70)
    b.birds = 3


def L_forest_deep(b: B):
    b.sky()
    b.celestial(0.3, 0.14)
    night = b.T["_name"] == "night"
    for i in range(6):
        b.prop("far", "tree", -0.05 + i * 0.22, b.ground - 0.1, s=0.9, kind="kalamkari", seed=40 + i, h=60, night=night)
    b.mist("far", b.ground - 0.12, 0.6)
    for i in range(5):
        b.prop("mid", "tree", 0.02 + i * 0.25 + b.r.uniform(-0.05, 0.05), b.ground - 0.04, s=1.2,
               kind=("banyan", "kalamkari", "peepal", "mango", "night")[i if not night else 4], seed=i, h=64, night=night)
    b.floor_band("grass", "#4a5a2a")
    b.prop("ground", "bush", 0.2, b.ground + 0.03, s=1.2, seed=5)
    b.prop("ground", "rock", 0.78, b.ground + 0.04, s=1.2, seed=7)
    b.prop("front", "tree", -0.06, 1.15, s=1.6, kind="kalamkari", seed=31, dark=0.6, h=70)
    b.prop("front", "bush", 1.04, 1.04, s=2.2, seed=9, dark=0.6)


def L_ashram(b: B):
    b.sky()
    b.celestial(0.8, 0.18)
    b.clouds(2)
    b.prop("far", "mountains", 0.5, b.ground - 0.14, s=1.0, color=b.T["far"], w=200, h=30, seed=8, snow=True)
    b.prop("mid", "tree", 0.12, b.ground - 0.03, s=1.1, kind="peepal", seed=3, h=64)
    b.prop("mid", "tree", 0.9, b.ground - 0.03, s=1.0, kind="mango", seed=4, h=56)
    b.prop("set", "hut", 0.7, b.ground - 0.01, s=1.3)
    b.prop("set", "hut", 0.86, b.ground - 0.02, s=0.95, roof="#c8a040")
    b.floor_band("earth", "#8a6a46")
    b.prop("ground", "yagya_kund", 0.42, b.ground + 0.06, s=0.8)
    b.flame(0.42, b.ground + 0.06 - 0.075, 2.0, kind="yagya")
    b.prop("ground", "pots", 0.62, b.ground + 0.05, s=0.9)
    b.prop("ground", "grass", 0.2, b.ground + 0.08, s=1.4, seed=2)
    b.prop("front", "bush", -0.03, 1.05, s=2.0, seed=12, dark=0.45)


def L_yagya_shala(b: B):
    b.sky()
    t = b.T["_name"]
    b.prop("set", "palace", 0.5, b.ground - 0.02, s=1.0, wall="#a8743a" if t != "night" else "#3a2a4a",
           window="#2a1a14", interior=True, curtains=False, bays=4, w=150, h=58, seed=2)
    b.floor_band("stone", "#8a6e4e")
    b.prop("ground", "yagya_kund", 0.5, b.ground + 0.07, s=1.2)
    b.flame(0.5, b.ground + 0.07 - 0.11, 3.0, kind="yagya")
    for x in (0.15, 0.85):
        b.prop("ground", "deepstambh", x, b.ground + 0.02, s=1.0)
        b.flame(x, b.ground + 0.02 - 0.232, 1.0)
    b.prop("ground", "pots", 0.3, b.ground + 0.08, s=0.8, n=3)
    b.prop("ground", "kalash" if False else "pots", 0.7, b.ground + 0.08, s=0.8, n=2)
    b.prop("sky", "toran", 0.5, 0.03, s=1.4, w=150)
    b.light_over = dict(spot=(0.5, 0.62), spot_color="#ffb060", rays=0.2)


def L_kailash(b: B):
    b.sky()
    b.celestial(0.72, 0.14)
    b.clouds(3, color="#eef0f2" if b.T["_name"] != "night" else None)
    b.prop("far", "mountains", 0.5, b.ground - 0.08, s=1.4, color="#8a98a8", w=170, h=48, seed=12, snow=True, peaks=5,
           style="sharp")
    b.prop("mid", "mountains", 0.3, b.ground - 0.02, s=1.0, color="#6a7888", w=160, h=28, seed=13, snow=True, peaks=4)
    b.prop("mid", "tree", 0.88, b.ground - 0.02, s=1.0, kind="pine", seed=1, h=48, leaf="#2f5a4a")
    b.prop("mid", "tree", 0.08, b.ground - 0.02, s=0.9, kind="pine", seed=2, h=44, leaf="#2f5a4a")
    b.floor_band("snow")
    b.prop("ground", "rock", 0.5, b.ground + 0.03, s=1.8, color="#8a8a90", seed=4)
    b.prop("ground", "rock", 0.82, b.ground + 0.07, s=1.2, color="#7a7a84", seed=5)


def L_kshirsagar(b: B):
    b.sky()
    b.clouds(3)
    b.celestial(0.5, 0.13)
    b.water_band(b.ground - 0.2, 1.0 + M, "#2f5a78", layer="mid")
    b.prop("set", "lotus", 0.2, b.ground - 0.02, s=1.0, n=3, seed=3)
    b.prop("set", "lotus", 0.82, b.ground, s=0.9, n=2, seed=4)
    b.floor = "water"
    b.light_over = dict(rays=0.6, spot=(0.5, 0.4))


def L_swarga(b: B):
    b.sky()
    b.clouds(4, color="#f6ecd4", y=0.1)
    b.prop("far", "city", 0.5, b.ground - 0.2, s=1.3, color="#f2e2b8", w=170, h=44, seed=5)
    b.prop("set", "palace", 0.5, b.ground - 0.04, s=0.95, wall="#e0c070", window="#f6ecd4", bays=5, w=150, h=60, seed=6)
    for x in (0.1, 0.5, 0.9):
        b.hang("cloud", x, b.ground + 0.02, s=1.8, string=0.0, color="#f6ecd4", parallax=1.2, kind="puffy", seed=int(x * 10))
    b.floor_band("floor", "#d8c08a")
    b.light_over = dict(rays=0.7)


def L_patala(b: B):
    b.sky()
    b.prop("far", "cave", 0.5, b.ground + 0.02, s=2.6, color="#2a2430", w=60, h=44)
    for i, x in enumerate((0.12, 0.88)):
        b.prop("mid", "pillar", x, b.ground, s=1.0, color="#4a4a5a", trim="#5a8a6a", h=60)
    b.floor_band("stone", "#3a3440")
    for i in range(6):
        x = 0.1 + i * 0.16
        b.prop("ground", "diya", x, b.ground + 0.06)
        b.flame(x, b.ground + 0.06 - 0.012, 0.6)
    b.light_over = dict(spot_color="#7ae0b0", spot=(0.5, 0.55))


def L_lanka(b: B):
    b.sky()
    b.celestial(0.8, 0.16)
    b.clouds(2)
    b.water_band(b.ground - 0.14, b.ground - 0.06, "#2f5a6a", layer="far")
    b.prop("mid", "fort", 0.5, b.ground - 0.04, s=1.0, gold=True, w=180, h=26, seed=4)
    b.prop("set", "tree", 0.06, b.ground - 0.01, s=1.0, kind="palm", seed=1, h=56)
    b.prop("set", "tree", 0.94, b.ground - 0.01, s=1.0, kind="palm", seed=2, h=50)
    b.floor_band("sand", "#a8844a")
    if b.T["_name"] == "fire":
        for i in range(7):
            b.flame(0.08 + i * 0.14, b.ground - 0.12 - b.r.uniform(0, 0.08), 4.0, parallax=0.55, kind="big")


def L_ocean_shore(b: B):
    b.sky()
    b.celestial(0.75, 0.2)
    b.clouds(3)
    b.water_band(b.ground - 0.16, b.ground + 0.0, "#2f5a78", layer="mid")
    b.prop("set", "setu", 0.6, b.ground - 0.04, s=1.3, w=140)
    b.prop("set", "tree", 0.05, b.ground - 0.0, s=1.1, kind="palm", seed=3, h=60)
    b.floor_band("sand", "#c8a46a")
    b.prop("ground", "rock", 0.2, b.ground + 0.04, s=1.5, seed=1)
    b.birds = 4


def L_kurukshetra(b: B):
    b.sky()
    b.celestial(0.62, 0.16)
    t = b.T["_name"]
    b.prop("far", "mountains", 0.5, b.ground - 0.13, s=1.0, color=b.T["far"], w=200, h=12, seed=21, peaks=9)
    # distant army: rows of pennants on poles + tents
    for i in range(22):
        x = -0.12 + i * 0.062 + b.r.uniform(-0.01, 0.01)
        b.prop("mid", "flagpole", x, b.ground - 0.12, s=0.55 + b.r.uniform(-0.05, 0.08),
               color=b.r.choice(["vermilion", "mustard", "saffron", "#2f5a8a"]), h=24)
    for i in range(5):
        b.prop("mid", "tent", 0.05 + i * 0.22 + b.r.uniform(-0.03, 0.03), b.ground - 0.1, s=0.6,
               c1=b.r.choice(["#e0a83a", "#d8c8a8"]), c2="vermilion")
    b.mist("mid", b.ground - 0.1, 0.55)
    for i, x in enumerate((0.1, 0.9)):
        b.prop("set", "flagpole", x, b.ground + 0.0, s=1.4, color="mustard", h=40, kind="banner",
               emblem="hanuman" if i == 0 else "#2f5a8a")
    b.floor_band("battle", "#6a4a34")
    if t in ("night", "fire"):
        for x in (0.2, 0.55, 0.8):
            b.flame(x, b.ground - 0.08, 1.4, parallax=0.6, kind="camp")
    b.birds = 6
    b.light_over = dict(dust=1.4)


def L_war_camp(b: B):
    b.sky()
    b.celestial(0.8, 0.14)
    for i in range(6):
        b.prop("mid", "tent", -0.05 + i * 0.21, b.ground - 0.06, s=0.95, c1=b.r.choice(["#e0a83a", "#c8b898"]),
               c2=b.r.choice(["vermilion", "#2f5a8a"]))
    b.floor_band("earth", "#5a4030")
    b.flame(0.5, b.ground + 0.06, 2.2, kind="camp")
    b.prop("ground", "rock", 0.5, b.ground + 0.075, s=0.7, seed=3, color="#4a3a30")
    b.prop("ground", "chariot", 0.85, b.ground + 0.02, s=1.0)


def L_ghats(b: B):
    b.sky()
    b.celestial(0.8, 0.2)
    b.clouds(2)
    b.prop("far", "city", 0.35, b.ground - 0.2, s=1.2, color="#e8e0d0", w=120, h=40, seed=9)
    b.prop("mid", "temple", 0.72, b.ground - 0.13, s=1.1, color="#c8a060")
    b.prop("set", "steps", 0.35, b.ground - 0.06, s=1.0, w=150, n=6, h=16)
    b.water_band(b.ground - 0.06, 1.0 + M, "#5a7a84", layer="set")
    b.prop("ground", "boat", 0.78, b.ground + 0.07, s=1.2, sail="#e8d8b4")
    b.prop("ground", "pots", 0.2, b.ground - 0.03, s=0.8)
    for x in (0.08, 0.28):
        b.prop("ground", "deepstambh", x, b.ground - 0.02, s=0.6)
        b.flame(x, b.ground - 0.02 - 0.13, 0.7)
    b.floor = "water"
    b.birds = 5


def L_village(b: B):
    b.sky()
    b.celestial(0.8, 0.18)
    b.clouds(2)
    b.prop("far", "mountains", 0.5, b.ground - 0.12, s=1.0, color=b.T["far"], w=200, h=20, seed=31)
    b.prop("mid", "tree", 0.08, b.ground - 0.04, s=1.1, kind="mango", seed=6, h=58)
    b.prop("mid", "tree", 0.92, b.ground - 0.04, s=1.0, kind="kalamkari", seed=7, h=54)
    for x, s in ((0.32, 1.0), (0.55, 1.2), (0.76, 0.9)):
        b.prop("set", "hut", x, b.ground - 0.02, s=s)
    b.floor_band("earth", "#9a7a4e")
    b.prop("ground", "pots", 0.15, b.ground + 0.05, s=0.9)
    b.prop("ground", "grass", 0.9, b.ground + 0.07, s=1.4)


def L_mountain_pass(b: B):
    b.sky()
    b.celestial(0.3, 0.16)
    b.clouds(3)
    b.prop("far", "mountains", 0.5, b.ground - 0.06, s=1.3, color=b.T["far"], w=180, h=46, seed=41, snow=True, style="sharp")
    b.prop("mid", "mountains", 0.5, b.ground - 0.0, s=1.0, color=shade(b.T["far"], -0.15), w=200, h=26, seed=42)
    b.prop("set", "sanjeevani_mountain", 0.78, b.ground - 0.01, s=0.9)
    b.prop("set", "tree", 0.12, b.ground - 0.01, s=0.9, kind="pine", h=46, seed=3, leaf="#3a5a3a")
    b.floor_band("stone", "#7a6a5a")
    b.prop("ground", "rock", 0.3, b.ground + 0.05, s=1.6, seed=8)


def L_cave(b: B):
    b.sky()
    b.prop("mid", "cave", 0.5, b.ground + 0.1, s=3.4, color="#3a302a", w=60, h=44)
    b.floor_band("dark", "#2a2018")
    b.flame(0.5, b.ground + 0.07, 1.8, kind="camp")
    b.prop("ground", "rock", 0.15, b.ground + 0.05, s=1.4, seed=11, color="#4a3e34")
    b.light_over = dict(spot=(0.5, 0.75), spot_color="#ff9a4a")


def L_dwarka(b: B):
    b.sky()
    b.celestial(0.18, 0.18)
    b.clouds(2)
    b.water_band(b.ground - 0.2, b.ground - 0.08, "#2f6a88", layer="far")
    b.prop("mid", "city", 0.5, b.ground - 0.07, s=1.4, color="#f0d890", w=150, h=40, seed=17)
    b.prop("set", "pillar", 0.08, b.ground, s=1.1, h=62)
    b.prop("set", "pillar", 0.92, b.ground, s=1.1, h=62)
    b.floor_band("floor", "#c8a870")
    b.prop("sky", "toran", 0.5, 0.03, s=1.4, w=150)


def L_vrindavan(b: B):
    b.sky()
    b.celestial(0.8, 0.18)
    b.clouds(2)
    b.water_band(b.ground - 0.1, b.ground - 0.04, "#2a4a7a", layer="mid")
    for i, x in enumerate((0.1, 0.42, 0.86)):
        b.prop("set", "tree", x, b.ground - 0.01, s=1.05, kind="kadamba", seed=60 + i, h=60)
    b.floor_band("grass", "#6a8a3a")
    b.prop("ground", "bush", 0.66, b.ground + 0.04, s=1.0, flowers="#f2a2b8", seed=3)
    b.prop("ground", "lotus", 0.3, b.ground + 0.08, s=0.7, n=2)
    b.birds = 3


def L_temple(b: B):
    b.sky()
    b.prop("set", "palace", 0.5, b.ground - 0.02, s=1.0, wall="#6a3a2a", window="#1a100c", interior=True, bays=3, w=150,
           h=64, seed=5, curtains=True)
    b.prop("set", "temple", 0.5, b.ground - 0.02, s=0.75, color="#c89a4a")
    b.floor_band("stone", "#6a5444")
    for x in (0.18, 0.32, 0.68, 0.82):
        b.prop("ground", "deepstambh", x, b.ground + 0.03, s=0.9)
        b.flame(x, b.ground + 0.03 - 0.21, 0.9)
    b.prop("sky", "toran", 0.5, 0.03, s=1.4, w=150)
    b.light_over = dict(spot=(0.5, 0.55), spot_color="#ffb060")


def L_shmashan(b: B):
    b.sky()
    b.celestial(0.8, 0.15)
    b.prop("mid", "tree", 0.15, b.ground - 0.03, s=1.1, kind="banyan", seed=8, h=64, night=True)
    b.prop("mid", "tree", 0.85, b.ground - 0.03, s=1.0, kind="kalamkari", seed=9, h=52, night=True)
    b.floor_band("dark", "#3a2c24")
    b.flame(0.6, b.ground + 0.04, 2.6, kind="pyre")
    b.prop("ground", "rock", 0.62, b.ground + 0.05, s=0.9, seed=2, color="#4a3a30")
    b.light_over = dict(spot=(0.6, 0.7), spot_color="#ff8a3a")


def L_cosmic(b: B):
    b.sky()
    c = b.L["far"]
    for k in range(4):
        x, y = b.r.uniform(0.1, 0.9), b.r.uniform(0.1, 0.6)
        neb = radial(int(b.W * 0.5), int(b.H * 0.5), b.W * 0.25, b.H * 0.25, b.W * 0.25,
                     b.r.choice(["#8a4ab8a0", "#4a7ad8a0", "#d84a8aa0"]), "#00000000", 1.2)
        c.img.alpha_composite(neb, (int((x + M) * b.W - b.W * 0.25), int((y + M) * b.H - b.H * 0.25)))
    for k in range(3):
        b.hang("sun", b.r.uniform(0.1, 0.9), b.r.uniform(0.1, 0.35), s=b.r.uniform(0.4, 0.7),
               color=b.r.choice(["#e8a63a", "#9ad0e6", "#e88aa0"]), rays="#c8a0e8")
    b.floor = "cosmic"
    b.light_over = dict(rays=0.4)


def L_plain(b: B):
    b.sky()
    b.celestial(0.7, 0.2)
    b.clouds(3)
    b.prop("far", "mountains", 0.5, b.ground - 0.1, s=1.0, color=b.T["far"], w=200, h=18, seed=51)
    b.prop("set", "tree", 0.15, b.ground - 0.01, s=0.9, kind="kalamkari", seed=5, h=50)
    b.floor_band("sand", "#b8945a")
    b.prop("ground", "rock", 0.75, b.ground + 0.05, s=1.1, seed=7)
    b.prop("ground", "grass", 0.4, b.ground + 0.06, s=1.2)
    b.birds = 4


def L_lotus_lake(b: B):
    b.sky()
    b.celestial(0.5, 0.16)
    b.clouds(3)
    b.prop("far", "mountains", 0.5, b.ground - 0.17, s=1.0, color=b.T["far"], w=200, h=20, seed=61)
    b.water_band(b.ground - 0.17, 1.0 + M, "#3f7a8a", layer="mid")
    for i in range(5):
        b.prop("set", "lotus", 0.1 + i * 0.2 + b.r.uniform(-0.04, 0.04), b.ground - 0.04 + b.r.uniform(0, 0.12), s=1.0,
               n=b.r.randint(1, 3), seed=i)
    b.floor = "water"
    b.birds = 2


def L_stage(b: B):
    """Empty puppet-theatre stage (use with the curtain intro)."""
    b.sky()
    c = b.L["mid"]
    d = ImageDraw.Draw(c.img)
    d.rectangle([0, 0, c.LW, c.LH], fill=rgb("#2a1a14"))
    b.prop("set", "pillar", 0.04, b.ground + 0.02, s=1.4, h=64, color="#e6dcc8")
    b.prop("set", "pillar", 0.96, b.ground + 0.02, s=1.4, h=64, color="#e6dcc8")
    b.floor_band("stage", "#4a2e1e")
    for i in range(12):
        x = 0.1 + i * 0.073
        b.prop("ground", "diya", x, b.ground + 0.02, s=0.8)
        b.flame(x, b.ground + 0.02 - 0.01, 0.5)


def L_shadow_screen(b: B):
    """Forest-night shadow-puppet (Tholu Bommalata) screen like the reference."""
    b.sky()
    b.celestial(0.72, 0.12)
    for i in range(5):
        b.prop("far", "tree", -0.05 + i * 0.26, b.ground - 0.06, s=1.2, kind="night", seed=70 + i, h=70, night=True)
    b.prop("mid", "tree", 0.92, b.ground - 0.02, s=1.0, kind="banana", seed=3, h=54, night=False)
    b.prop("set", "screen", 0.42, b.ground - 0.12, s=1.0, w=60, h=38,
           lit="#efe0b8" if b.T["_name"] != "fire" else "#e8a060")
    b.floor_band("dark", "#2a2018")
    b.flame(0.42, b.ground + 0.03, 1.6, kind="camp")
    b.light_over = dict(spot=(0.42, 0.5), spot_color="#ffcf8a")


LOCALES = {
    "palace_court": (L_palace_court, ["day", "night", "dusk", "divine"], "राजदरबार (Ayodhya/Hastinapur darbar)"),
    "palace_garden": (L_palace_garden, ["day", "dawn", "dusk", "night"], "राजउद्यान / अशोक वाटिका"),
    "forest_banana": (L_forest_banana, ["day", "dawn", "dusk", "night"], "कदली वन (banana forest)"),
    "forest_deep": (L_forest_deep, ["day", "dusk", "night", "storm"], "घना वन / दण्डकारण्य"),
    "ashram": (L_ashram, ["dawn", "day", "dusk", "night"], "ऋषि आश्रम (hut, yagya)"),
    "yagya_shala": (L_yagya_shala, ["day", "night", "dawn", "divine"], "यज्ञशाला (agni yagya hall)"),
    "kailash": (L_kailash, ["snow", "dawn", "night", "divine"], "कैलाश पर्वत"),
    "kshirsagar": (L_kshirsagar, ["divine", "day", "night", "cosmic"], "क्षीरसागर / वैकुण्ठ"),
    "swarga": (L_swarga, ["divine", "day", "dusk", "night"], "स्वर्ग / इन्द्रलोक"),
    "patala": (L_patala, ["night", "fire", "cosmic", "dusk"], "पाताल लोक"),
    "lanka": (L_lanka, ["day", "dusk", "night", "fire"], "सोने की लंका"),
    "ocean_shore": (L_ocean_shore, ["day", "dawn", "dusk", "night"], "समुद्र तट / राम सेतु"),
    "kurukshetra": (L_kurukshetra, ["dawn", "day", "dusk", "night", "fire", "storm"], "कुरुक्षेत्र युद्धभूमि"),
    "war_camp": (L_war_camp, ["night", "dusk", "dawn", "fire"], "युद्ध शिविर"),
    "ghats": (L_ghats, ["dawn", "day", "dusk", "night"], "गंगा घाट"),
    "village": (L_village, ["day", "dawn", "dusk", "night"], "गाँव / गोकुल"),
    "mountain_pass": (L_mountain_pass, ["day", "dusk", "night", "snow"], "गंधमादन / हिमालय (sanjeevani)"),
    "cave": (L_cave, ["night", "fire", "day", "cosmic"], "गुफा"),
    "dwarka": (L_dwarka, ["day", "dusk", "night", "divine"], "द्वारका"),
    "vrindavan": (L_vrindavan, ["day", "dawn", "dusk", "night"], "वृन्दावन / यमुना तट"),
    "temple": (L_temple, ["night", "day", "dusk", "divine"], "मंदिर गर्भगृह"),
    "shmashan": (L_shmashan, ["night", "fire", "storm", "dusk"], "श्मशान"),
    "cosmic": (L_cosmic, ["cosmic", "divine", "night", "fire"], "ब्रह्माण्ड / विराट रूप"),
    "plain": (L_plain, ["day", "dusk", "dawn", "storm"], "खुला मैदान / मार्ग"),
    "lotus_lake": (L_lotus_lake, ["day", "dawn", "divine", "night"], "कमल सरोवर"),
    "stage": (L_stage, ["night", "day", "fire", "divine"], "कठपुतली मंच (theatre stage)"),
    "shadow_screen": (L_shadow_screen, ["night", "fire", "dusk", "cosmic"], "छाया-नाट्य परदा (shadow theatre)"),
}


# ambient life per locale: (who, mode, kwargs, times-or-None)
LIFE = {
    "forest_banana": [("deer", "run_across", dict(depth=0.62, period=11, speed=0.32), ("day", "dawn", "dusk")),
                      ("butterfly", "hover", dict(depth=0.95, y=0.6), ("day", "dawn")),
                      ("golden_deer", "graze", dict(depth=0.58, x=0.84), ("dawn",)),
                      ("peacock", "walk_across", dict(depth=0.72, period=16, speed=0.06), ("day",))],
    "forest_deep": [("deer", "graze", dict(depth=0.6, x=0.18), ("day", "dusk")), ("tiger", "walk_across", dict(depth=0.6, period=18, speed=0.07), ("dusk", "night")),
                    ("wolf", "run_across", dict(depth=0.6, period=13, speed=0.25), ("night",)), ("owl", "perch", dict(depth=0.7, x=0.2, y=0.5), ("night",)),
                    ("monkey_animal", "run_across", dict(depth=0.66, period=12, speed=0.22), ("day",))],
    "palace_garden": [("peacock", "walk_across", dict(depth=0.7, period=15, speed=0.06), ("day", "dawn", "dusk")),
                      ("hamsa", "glide", dict(depth=0.8, speed=0.025), ("day", "dawn", "dusk")),
                      ("butterfly", "hover", dict(depth=0.95, y=0.62), ("day", "dawn")), ("parrot", "fly_across", dict(depth=0.8, period=9, speed=0.2), ("day",))],
    "ashram": [("cow", "graze", dict(depth=0.66, x=0.14), ("dawn", "day", "dusk")), ("deer", "graze", dict(depth=0.6, x=0.9), ("dawn", "day")),
               ("peacock", "walk_across", dict(depth=0.75, period=18, speed=0.05), ("day",)), ("parrot", "fly_across", dict(depth=0.8, period=10, speed=0.2), ("dawn", "day"))],
    "vrindavan": [("cow", "graze", dict(depth=0.64, x=0.2), None), ("calf", "walk_across", dict(depth=0.66, period=20, speed=0.05), ("day", "dawn")),
                  ("peacock", "walk_across", dict(depth=0.72, period=14, speed=0.06), ("day", "dawn", "dusk")),
                  ("parrot", "fly_across", dict(depth=0.8, period=8, speed=0.22), ("day",)), ("butterfly", "hover", dict(depth=0.95, y=0.6), ("day",))],
    "village": [("cow", "walk_across", dict(depth=0.64, period=22, speed=0.05), ("day", "dawn")), ("dog", "run_across", dict(depth=0.75, period=14, speed=0.2), ("day",)),
                ("hen", "peck", dict(depth=0.85, x=0.86), ("day", "dawn")), ("rooster", "peck", dict(depth=0.85, x=0.78), ("dawn",))],
    "kurukshetra": [("kaurava_soldier", "march", dict(depth=0.55, period=9, speed=0.05, n=3), ("dawn", "day", "dusk")),
                    ("chariot_horse", "run_across", dict(depth=0.52, period=10, speed=0.3), ("dawn", "day", "dusk")),
                    ("vulture", "circle", dict(depth=0.6, y=0.22), ("dusk", "day", "fire"))],
    "war_camp": [("horse", "graze", dict(depth=0.62, x=0.12), None), ("dog", "walk_across", dict(depth=0.7, period=20, speed=0.06), ("dusk", "dawn"))],
    "ghats": [("hamsa", "glide", dict(depth=0.82, speed=0.02), ("dawn", "day", "dusk")), ("matsya_fish", "leap", dict(depth=0.85, period=6), ("day", "dawn")),
              ("crane", "perch", dict(depth=0.78, x=0.9), ("dawn", "day"))],
    "lotus_lake": [("hamsa", "glide", dict(depth=0.8, speed=0.022), None), ("fish", "leap", dict(depth=0.85, period=5), ("day", "dawn", "divine")),
                   ("kingfisher", "fly_across", dict(depth=0.85, period=9, speed=0.25), ("day",)), ("butterfly", "hover", dict(depth=0.95, y=0.55), ("day", "divine"))],
    "kshirsagar": [("fish", "leap", dict(depth=0.82, period=5.5), ("day", "divine")), ("hamsa", "glide", dict(depth=0.8, speed=0.02), ("day", "divine"))],
    "ocean_shore": [("fish", "leap", dict(depth=0.7, period=6, y=0.73), ("day", "dawn", "dusk")), ("kite", "circle", dict(depth=0.6, y=0.2), ("day", "dusk"))],
    "dwarka": [("kite", "circle", dict(depth=0.6, y=0.2), ("day", "dusk"))],
    "mountain_pass": [("eagle", "circle", dict(depth=0.6, y=0.18), ("day", "dusk")), ("goat", "graze", dict(depth=0.66, x=0.2), ("day",))],
    "kailash": [("eagle", "circle", dict(depth=0.6, y=0.18), ("snow", "dawn"))],
    "plain": [("deer", "run_across", dict(depth=0.6, period=12, speed=0.3), ("day", "dawn")), ("jackal", "walk_across", dict(depth=0.62, period=16, speed=0.07), ("dusk",)),
              ("camel", "walk_across", dict(depth=0.55, period=24, speed=0.03), ("day",))],
    "shmashan": [("jackal", "walk_across", dict(depth=0.62, period=15, speed=0.06), None), ("crow", "peck", dict(depth=0.85, x=0.82), None),
                 ("bat", "hover", dict(depth=0.8, y=0.3), ("night",))],
    "cave": [("bat", "hover", dict(depth=0.8, y=0.3), None)],
    "swarga": [("hamsa", "fly_across", dict(depth=0.75, period=9, speed=0.12), None), ("butterfly", "hover", dict(depth=0.95, y=0.5), ("divine", "day"))],
    "palace_court": [("pigeon", "fly_across", dict(depth=0.7, period=13, speed=0.18), ("day",))],
    "temple": [("pigeon", "fly_across", dict(depth=0.7, period=14, speed=0.18), ("day",))],
    "lanka": [("lanka_soldier", "march", dict(depth=0.5, period=10, speed=0.04, n=2, y=0.62), ("day", "dusk", "night"))],
    "patala": [("cobra", "graze", dict(depth=0.7, x=0.15), None)],
    "yagya_shala": [], "cosmic": [], "stage": [], "shadow_screen": [],
}

FLORA = {"forest_banana": 1.2, "forest_deep": 1.0, "palace_garden": 1.0, "ashram": 1.1, "vrindavan": 1.3, "village": 0.8,
         "mountain_pass": 0.5, "plain": 0.9, "lotus_lake": 0.0, "kurukshetra": 0.4, "war_camp": 0.4, "shmashan": 0.4,
         "kailash": 0.0}
WIND = {"forest_banana", "palace_garden", "vrindavan", "plain", "ashram", "village", "mountain_pass", "kurukshetra", "lotus_lake"}


def list_envs():
    out = []
    for loc, (_, times, desc) in LOCALES.items():
        for t in times:
            out.append((f"{loc}_{t}", desc, t))
    return out


def parse_env_id(env_id):
    for loc in sorted(LOCALES, key=len, reverse=True):
        if env_id == loc:
            return loc, LOCALES[loc][1][0]
        if env_id.startswith(loc + "_"):
            t = env_id[len(loc) + 1:]
            if t in TIMES:
                return loc, t
    raise KeyError(f"unknown environment '{env_id}'. Run: mythic.py list envs")


def build_env(env_id, W, H, seed=0, use_cache=True, overrides=None) -> Env:
    loc, t = parse_env_id(env_id)
    key = stable_hash({"e": env_id, "W": W, "H": H, "s": seed, "o": overrides or {}, "v": ENV_VERSION})
    cp = CACHE_DIR / "envs" / f"{env_id}_{W}x{H}_{key}.pkl"
    if use_cache and cp.exists():
        try:
            with open(cp, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    T = dict(TIMES[t])
    T["_name"] = t
    if overrides:
        T.update({k: v for k, v in overrides.items() if k in T})
    b = B(W, H, T, (env_id, seed))
    LOCALES[loc][0](b)
    # living background: flora, drifting clouds, ambient creatures
    if FLORA.get(loc, 0) > 0 and b.floor in ("grass", "earth", "sand", "battle", "dark", "stone"):
        b.flora(FLORA[loc])
    if t not in ("cosmic",) and loc not in ("stage", "cave", "temple", "palace_court", "yagya_shala", "patala", "shadow_screen"):
        b.drift_cloud(2 if t != "night" else 1, wind=(loc in WIND and t in ("day", "dawn", "dusk")))
    for who, mode, kw, times in LIFE.get(loc, []):
        if times is None or t in times:
            b.creature(who, mode, **kw)
    # depth blur: far layers softer, foreground soft (theatrical depth of field)
    layers = []
    for name, par in LAYERS:
        im = b.L[name].img
        if name == "far":
            im = im.filter(ImageFilter.GaussianBlur(max(1, H / 900)))
        elif name == "front":
            im = im.filter(ImageFilter.GaussianBlur(max(2, H / 280)))
        # keep every layer slot (even if empty): animated props, life & hanging props hook onto them
        layers.append((name, par, im if im.getbbox() else None))
    light = dict(vignette=T["vign"], haze=T["haze"], light=T["light"], amb=T["amb"], rays=T["rays"],
                 particles=T["particles"], spot=(0.5, 0.42), spot_color=T["light"], time=t)
    light.update(b.light_over)
    env = Env(env_id, W, H, layers, b.hanging, b.flames, b.water, b.birds, light, b.ground, b.floor,
              anim=b.anim, life=b.life, drift=b.drift)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with open(cp, "wb") as f:
            pickle.dump(env, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return env
