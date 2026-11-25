"""Jointed-puppet rig: parts with pivots, forward kinematics, rendering, strings."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from PIL import Image, ImageDraw

from .gfx import Sprite, affine_paste, drop_shadow_and_glow
from .util import rgb


@dataclass
class Part:
    name: str
    sprite: Sprite
    parent: str | None = None
    joint: tuple = (0.0, 0.0)      # pivot position in parent's local units
    z: int = 0
    rest: float = 0.0              # rest angle (deg, clockwise +)
    world: float | None = None     # if set, keep this absolute world angle (upright items)
    flipped: Sprite | None = None  # cached mirrored sprite
    visible: bool = True


@dataclass
class Rig:
    name: str
    ppu: float                     # sprite pixels per unit
    parts: dict = field(default_factory=dict)
    anchors: dict = field(default_factory=dict)   # string anchors: name -> (part, (ux, uy))
    ground: float = 48.0           # units from root down to ground contact
    extent: tuple = (-40, -80, 40, 55)  # rough bounds in units (for canvas sizing)
    meta: dict = field(default_factory=dict)
    order: list = field(default_factory=list)

    def add(self, part: Part):
        self.parts[part.name] = part
        self.order = sorted(self.parts.values(), key=lambda p: p.z)
        return part

    def remove(self, name):
        self.parts.pop(name, None)
        self.order = sorted(self.parts.values(), key=lambda p: p.z)

    # ------------------------------------------------------------------ FK
    def solve(self, pose: dict):
        """Return {name: (ux, uy, ang)} world-in-root-units transforms."""
        out = {}

        def get(name):
            if name in out:
                return out[name]
            p = self.parts[name]
            ang_local = p.rest + pose.get(name, 0.0)
            if p.parent is None:
                x, y, a = p.joint[0], p.joint[1], ang_local + pose.get("_root", 0.0)
            else:
                px, py, pa = get(p.parent)
                c, s = math.cos(math.radians(pa)), math.sin(math.radians(pa))
                jx, jy = p.joint
                x, y = px + c * jx - s * jy, py + s * jx + c * jy
                a = pa + ang_local
            if p.world is not None:
                a = p.world + pose.get(name + ".w", 0.0) + pose.get("_root", 0.0)
            out[name] = (x, y, a)
            return out[name]

        for n in self.parts:
            get(n)
        return out

    def anchor_world(self, solved, anchor):
        part, (ux, uy) = self.anchors[anchor]
        x, y, a = solved[part]
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        return x + c * ux - s * uy, y + s * ux + c * uy

    # ------------------------------------------------------------------ render
    def render(self, pose: dict, scale_px: float, flip=False, hidden=(), swaps=None, show=()):
        """Render to its own RGBA canvas. scale_px = output px per unit.
        Returns (image, origin_x, origin_y, solved) where origin is root pos in image."""
        k = scale_px / self.ppu
        x0, y0, x1, y1 = self.extent
        pad = 4
        W = int((x1 - x0) * scale_px) + 2 * pad
        H = int((y1 - y0) * scale_px) + 2 * pad
        if flip:
            ox = int(x1 * scale_px) + pad
        else:
            ox = int(-x0 * scale_px) + pad
        oy = int(-y0 * scale_px) + pad
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        solved = self.solve(pose)
        sgn = -1 if flip else 1
        swaps = swaps or {}
        for p in self.order:
            if (not p.visible and p.name not in show) or p.name in hidden:
                continue
            spr = swaps.get(p.name, p.sprite)
            ux, uy, a = solved[p.name]
            if flip:
                if spr is p.sprite:
                    if p.flipped is None:
                        p.flipped = p.sprite.flipped()
                    spr = p.flipped
                else:
                    spr = spr.flipped()
            affine_paste(canvas, spr, ox + sgn * ux * scale_px, oy + uy * scale_px, sgn * a, k, k)
        return canvas, ox, oy, solved


def draw_strings(frame: Image.Image, points, color="#efe3c4", alpha=90, width=1, top=-5, sway_px=0.0):
    """Puppet strings from attachment points straight up to the control bar."""
    d = ImageDraw.Draw(frame)
    c = rgb(color)[:3] + (alpha,)
    for (x, y) in points:
        d.line([(x + sway_px, top), (x, y)], fill=c, width=width)


def composite_puppet(frame, canvas, ox, oy, root_x, root_y, shadow=True, glow=None, alpha=1.0,
                     shadow_px=(12, 10, 0.42, 10)):
    """Place a rendered puppet canvas (with root at ox,oy) at root_x,root_y on frame."""
    img = canvas
    if shadow or glow:
        img = drop_shadow_and_glow(canvas, shadow_px if shadow else None, glow)
    if alpha < 0.999:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(round(root_x - ox)), int(round(root_y - oy))
    fw, fh = frame.size
    w, h = img.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, fw - x), min(h, fh - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, w, h):
        img = img.crop((sx0, sy0, sx1, sy1))
    frame.alpha_composite(img, (x + sx0, y + sy0))
