"""Puppet-theatre proscenium: red velvet curtain, scalloped valance, pillars,
diya footlights and audience silhouettes.  `Curtain.overlay(img, k_open, T)`
draws it over a frame (k_open 0 = closed, 1 = fully open & pushed past)."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .gfx import Pen, linear_gradient, soft_dot, paper, arc_pts
from .props import build_prop
from .render import flame_frames
from .gfx import affine_paste
from .util import rgb, shade, rng


class Curtain:
    def __init__(self, W, H, color="#8e1a1e"):
        self.W, self.H = W, H
        U = min(H, W * 1.15) / 100.0
        self.U = U
        # velvet panel (half width + overlap) with vertical folds
        pw, ph = int(W * 0.56), int(H * 0.86)
        xs = np.linspace(0, 1, pw, dtype=np.float32)
        folds = 0.62 + 0.38 * np.cos(xs * math.pi * 2 * 9) ** 2
        folds *= 0.85 + 0.15 * np.cos(xs * math.pi * 2 * 2.3)
        c = np.array(rgb(color)[:3], np.float32)
        arr = np.clip(folds[None, :, None] * c[None, None, :] * np.ones((ph, 1, 1), np.float32), 0, 255).astype(np.uint8)
        panel = Image.fromarray(arr, "RGB").convert("RGBA")
        grad = linear_gradient(pw, ph, [(0, "#00000060"), (0.25, "#00000000"), (0.85, "#00000020"), (1, "#00000070")])
        panel.alpha_composite(grad)
        d = ImageDraw.Draw(panel)
        d.line([(0, ph - 3), (pw, ph - 3)], fill=rgb("#d8a83a"), width=max(2, int(H / 300)))
        self.panel = panel
        self.panel_ph = ph
        # valance with scallops
        vh = int(H * 0.13)
        val = Image.new("RGBA", (W, vh + int(H * 0.04)), (0, 0, 0, 0))
        dv = ImageDraw.Draw(val)
        dv.rectangle([0, 0, W, vh], fill=rgb(shade(color, -0.12)))
        n = 7
        sw = W * 0.8 / n
        x0 = W * 0.1
        for k in range(n):
            bx = x0 + k * sw
            dv.pieslice([bx, vh - sw * 0.28, bx + sw, vh + sw * 0.28], 0, 180, fill=rgb(shade(color, -0.12)))
            dv.arc([bx, vh - sw * 0.28, bx + sw, vh + sw * 0.28], 0, 180, fill=rgb("#d8a83a"), width=max(2, int(H / 400)))
        self.valance = val
        # pillars
        self.pillar = build_prop("pillar", U * 1.35, h=66, color="#e6dcc8", trim="#c8a050")
        # floor strip, audience heads
        self.floor_h = int(H * 0.11)
        fl = paper(W, self.floor_h, base="#3a2416", seed=4, strength=1.2)
        ImageDraw.Draw(fl).line([(0, 1), (W, 1)], fill=rgb("#c8a050"), width=max(2, int(H / 400)))
        self.floor = fl
        aud = Image.new("RGBA", (W, int(H * 0.12)), (0, 0, 0, 0))
        da = ImageDraw.Draw(aud)
        r = rng("aud")
        ah = aud.size[1]
        for k in range(40):
            x = r.uniform(0, W)
            rr = r.uniform(0.022, 0.032) * H
            y = ah - rr * r.uniform(0.6, 1.2)
            da.ellipse([x - rr, y - rr * 1.1, x + rr, y + rr * 1.1], fill=(14, 9, 7, 235))
            da.ellipse([x - rr * 2.2, y + rr * 0.7, x + rr * 2.2, y + rr * 3.6], fill=(14, 9, 7, 235))
        self.audience = aud.filter(ImageFilter.GaussianBlur(max(1, H / 500)))

    def overlay(self, img: Image.Image, k: float, T: float) -> Image.Image:
        """k: 0 closed .. 1 open. While opening the whole proscenium pushes in & fades."""
        W, H = self.W, self.H
        base = img.convert("RGBA")
        stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # dark backstage surround
        d = ImageDraw.Draw(stage)
        top = int(H * 0.06)
        floor_y = int(H * 0.86)
        d.rectangle([0, 0, W, top], fill=(30, 18, 12, 255))
        d.rectangle([0, 0, int(W * 0.08), H], fill=(30, 18, 12, 255))
        d.rectangle([int(W * 0.92), 0, W, H], fill=(30, 18, 12, 255))
        # curtain panels slide to the sides (gathered = narrower)
        g = k
        pw = self.panel.size[0]
        lw = max(4, int(pw * (1 - 0.82 * g)))
        left = self.panel.resize((lw, self.panel_ph), Image.BILINEAR)
        right = left.transpose(Image.FLIP_LEFT_RIGHT)
        stage.alpha_composite(left, (int(W * 0.07), top))
        stage.alpha_composite(right, (int(W * 0.93) - lw, top))
        stage.alpha_composite(self.valance, (0, top - int(H * 0.02)))
        stage.alpha_composite(self.floor, (0, floor_y))
        for x in (0.045, 0.955):
            affine_paste(stage, self.pillar, x * W, floor_y + H * 0.005, 0, 1, 1)
        # diya footlights
        fr = flame_frames(int(H * 0.02) // 2 * 2, "lamp")
        n = 13
        for i in range(n):
            x = W * (0.17 + i * 0.66 / (n - 1))
            y = floor_y + H * 0.02
            dl = soft_dot(int(H * 0.025), "#ffb050", 120)
            stage.alpha_composite(dl, (int(x - dl.size[0] / 2), int(y - dl.size[1] * 0.7)))
            affine_paste(stage, fr[int(T * 10 + i) % len(fr)], x, y, 0, 1, 1)
        stage.alpha_composite(self.audience, (0, H - self.audience.size[1]))
        # push-in: scale proscenium around centre and fade it as it opens fully
        push = 1.0 + 0.55 * max(0.0, (k - 0.55) / 0.45) ** 1.5
        if push > 1.001:
            nw, nh = int(W * push), int(H * push)
            big = stage.resize((nw, nh), Image.BILINEAR)
            stage = big.crop(((nw - W) // 2, int((nh - H) * 0.45), (nw - W) // 2 + W, int((nh - H) * 0.45) + H))
        fade = 1.0 - max(0.0, (k - 0.75) / 0.25)
        if fade < 0.999:
            stage.putalpha(stage.getchannel("A").point(lambda v: int(v * fade)))
        # light from the footlights on the curtain
        base.alpha_composite(stage)
        return base.convert("RGB")
