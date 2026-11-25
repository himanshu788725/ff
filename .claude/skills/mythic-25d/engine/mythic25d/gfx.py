"""Painted-cutout drawing toolkit.

Everything is drawn with simple vector calls in *units* on a super-sampled
canvas (`Pen`), then `Pen.finish()` turns it into a `Sprite`: down-sampled
(anti-aliased), gouache-textured, edge-shaded and outlined like a cut paper
puppet part.  Sprites carry a pivot so the rig can rotate them at joints.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .util import rgb, shade, mix, rng

SS = 3  # super-sampling factor for all vector drawing


# =========================================================================== curves

def catmull(pts, closed=True, n=10):
    """Centripetal-ish Catmull-Rom through control points -> dense polyline."""
    pts = [tuple(map(float, p)) for p in pts]
    if len(pts) < 3:
        return pts
    out = []
    m = len(pts)
    rng_ = range(m) if closed else range(m - 1)
    for i in rng_:
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(pts[-1])
    return out


def bezier(p0, p1, p2, p3, n=16):
    out = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def arc_pts(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def limb(p0, p1, w0, w1, n=6):
    """Tapered limb polygon from p0 (width w0) to p1 (width w1), rounded ends."""
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang), math.cos(ang)
    left = [(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2)]
    right = [(x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)]
    cap1 = [(x1 + w1 / 2 * math.cos(ang + math.pi / 2 - math.pi * k / n),
             y1 + w1 / 2 * math.sin(ang + math.pi / 2 - math.pi * k / n)) for k in range(1, n)]
    cap0 = [(x0 + w0 / 2 * math.cos(ang - math.pi / 2 - math.pi * k / n),
             y0 + w0 / 2 * math.sin(ang - math.pi / 2 - math.pi * k / n)) for k in range(1, n)]
    return left + cap1 + right + cap0


def rot(pts, ang_deg, cx=0.0, cy=0.0):
    a = math.radians(ang_deg)
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def move(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def scale_pts(pts, sx, sy=None, cx=0.0, cy=0.0):
    sy = sx if sy is None else sy
    return [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in pts]


def mirror_x(pts):
    return [(-x, y) for x, y in pts]


# =========================================================================== noise / textures

@lru_cache(maxsize=32)
def noise(w, h, cell=64, octaves=4, seed=0):
    """Fractal value noise in [0,1] as float32 array (h, w)."""
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    c = cell
    for _ in range(octaves):
        gw, gh = max(2, w // max(1, c) + 2), max(2, h // max(1, c) + 2)
        g = (r.random((gh, gw)) * 255).astype(np.uint8)
        im = Image.fromarray(g, "L").resize((w + c, h + c), Image.BICUBIC)
        ox, oy = int(r.integers(0, max(1, c))), int(r.integers(0, max(1, c)))
        acc += amp * (np.asarray(im, np.float32)[oy:oy + h, ox:ox + w] / 255.0)
        tot += amp
        amp *= 0.5
        c = max(2, c // 2)
    return acc / tot


def grain_tile(size=512, seed=7):
    """Paper/gouache grain multiplier tile, mean ~1."""
    n1 = noise(size, size, 48, 4, seed)
    n2 = noise(size, size, 6, 2, seed + 1)
    g = 0.94 + 0.10 * n1 + 0.06 * (n2 - 0.5)
    return g.astype(np.float32)


def tile_to(arr, w, h):
    th, tw = arr.shape[:2]
    reps = (math.ceil(h / th), math.ceil(w / tw)) + ((1,) if arr.ndim == 3 else ())
    return np.tile(arr, reps)[:h, :w]


def paper(w, h, base="paper", seed=1, strength=1.0, fibers=True):
    """Aged paper / painted wall texture as RGBA image."""
    b = np.array(rgb(base)[:3], np.float32)
    n = noise(w, h, max(8, w // 6), 5, seed)
    m = noise(w, h, 5, 2, seed + 3)
    k = 1.0 + strength * (0.16 * (n - 0.5) + 0.07 * (m - 0.5))
    arr = np.clip(b[None, None, :] * k[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    if fibers:
        d = ImageDraw.Draw(im)
        r = rng("fibers", w, h, seed)
        for _ in range(int(w * h / 9000 * strength)):
            x, y = r.uniform(0, w), r.uniform(0, h)
            a = r.uniform(0, math.pi)
            ln = r.uniform(3, 14)
            c = shade(base, r.uniform(-0.18, 0.12))
            d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=c[:3] + (70,), width=1)
    return im


def linear_gradient(w, h, stops, vertical=True):
    """stops: list of (pos 0..1, colour)."""
    n = h if vertical else w
    t = np.linspace(0, 1, n, dtype=np.float32)
    cols = np.zeros((n, 4), np.float32)
    ps = [s[0] for s in stops]
    for ch in range(4):
        cols[:, ch] = np.interp(t, ps, [rgb(s[1])[ch] for s in stops])
    if vertical:
        arr = np.repeat(cols[:, None, :], w, axis=1)
    else:
        arr = np.repeat(cols[None, :, :], h, axis=0)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def radial(w, h, cx, cy, r, inner, outer, power=1.6):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.clip(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1.0, r), 0, 1) ** power
    a, b = np.array(rgb(inner), np.float32), np.array(rgb(outer), np.float32)
    arr = a[None, None, :] * (1 - d[..., None]) + b[None, None, :] * d[..., None]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


@lru_cache(maxsize=64)
def soft_dot(radius, color="#fff2c8", alpha=255, hard=0.0):
    s = int(radius * 2 + 4)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / max(0.5, radius)
    a = np.clip(1 - d, 0, 1)
    a = a ** (1.8 - hard * 1.5)
    c = rgb(color)
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = c[0], c[1], c[2]
    arr[..., 3] = (a * alpha).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# =========================================================================== sprite

@dataclass
class Sprite:
    img: Image.Image
    px: float = 0.0  # pivot in image pixels
    py: float = 0.0

    @property
    def size(self):
        return self.img.size

    def scaled(self, k):
        if abs(k - 1) < 1e-3:
            return self
        w, h = self.img.size
        nw, nh = max(1, round(w * k)), max(1, round(h * k))
        return Sprite(self.img.resize((nw, nh), Image.LANCZOS), self.px * nw / w, self.py * nh / h)

    def flipped(self):
        return Sprite(self.img.transpose(Image.FLIP_LEFT_RIGHT), self.img.size[0] - self.px, self.py)

    def tinted(self, color, amount):
        """Blend RGB toward a colour (used for depth/fog and silhouettes)."""
        c = Image.new("RGBA", self.img.size, rgb(color)[:3] + (255,))
        rgbim = Image.blend(self.img, c, amount)
        rgbim.putalpha(self.img.getchannel("A"))
        return Sprite(rgbim, self.px, self.py)

    def silhouette(self, color="#14100c"):
        im = Image.new("RGBA", self.img.size, rgb(color)[:3] + (255,))
        im.putalpha(self.img.getchannel("A"))
        return Sprite(im, self.px, self.py)

    def with_alpha(self, a):
        if a >= 0.999:
            return self
        im = self.img.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        return Sprite(im, self.px, self.py)


def blur_alpha_fast(alpha: Image.Image, radius: float, down=4):
    """Gaussian blur of an L image computed at reduced resolution (cheap glow/shadow)."""
    w, h = alpha.size
    sw, sh = max(1, w // down), max(1, h // down)
    small = alpha.resize((sw, sh), Image.BILINEAR).filter(ImageFilter.GaussianBlur(max(0.5, radius / down)))
    return small.resize((w, h), Image.BILINEAR)


# =========================================================================== pen

class Pen:
    """Vector pen working in *units*; origin (0,0) becomes the sprite pivot.

    bounds = (x0, y0, x1, y1) in units; ppu = output pixels per unit.
    """

    def __init__(self, bounds, ppu, ss=SS):
        x0, y0, x1, y1 = bounds
        self.ppu, self.ss = ppu, ss
        self.s = ppu * ss
        self.x0, self.y0 = x0, y0
        self.W = max(4, int(math.ceil((x1 - x0) * self.s)))
        self.H = max(4, int(math.ceil((y1 - y0) * self.s)))
        self.img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    # -- coordinate helpers
    def P(self, pts):
        s, x0, y0 = self.s, self.x0, self.y0
        return [((x - x0) * s, (y - y0) * s) for x, y in pts]

    def L(self, v):
        return max(1, int(round(v * self.s)))

    # -- primitives
    def poly(self, pts, fill, smooth=False, outline=None, w=0.0, n=10):
        if smooth:
            pts = catmull(pts, True, n)
        P = self.P(pts)
        if len(P) < 3:
            return
        self.d.polygon(P, fill=rgb(fill) if fill is not None else None)
        if outline is not None and w > 0:
            self.d.line(P + [P[0]], fill=rgb(outline), width=self.L(w), joint="curve")

    def line(self, pts, color, w, smooth=False, closed=False, n=10):
        if smooth:
            pts = catmull(pts, closed, n)
        P = self.P(pts)
        if closed:
            P = P + [P[0]]
        if len(P) >= 2:
            self.d.line(P, fill=rgb(color), width=self.L(w), joint="curve")
            # round caps
            r = self.L(w) / 2
            if r >= 2 and not closed:
                for (x, y) in (P[0], P[-1]):
                    self.d.ellipse([x - r, y - r, x + r, y + r], fill=rgb(color))

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, w=0.0):
        (X, Y), = self.P([(cx, cy)])
        RX, RY = rx * self.s, ry * self.s
        self.d.ellipse([X - RX, Y - RY, X + RX, Y + RY], fill=rgb(fill) if fill is not None else None,
                       outline=rgb(outline) if outline is not None else None,
                       width=self.L(w) if outline is not None else 0)

    def circle(self, cx, cy, r, fill=None, outline=None, w=0.0):
        self.ellipse(cx, cy, r, r, fill, outline, w)

    def arc(self, cx, cy, rx, ry, a0, a1, color, w):
        self.line(arc_pts(cx, cy, rx, ry, a0, a1), color, w)

    def rivet(self, x, y, r=0.9, color="gold"):
        """Puppet joint rivet: the signature of the jointed paper puppet."""
        self.circle(x, y, r * 1.25, fill="ink")
        self.circle(x, y, r, fill=color)
        self.circle(x - r * 0.3, y - r * 0.3, r * 0.32, fill=shade(color, 0.6))

    # -- clipped pattern fills
    def mask_of(self, pts, smooth=False, n=10):
        m = Image.new("L", (self.W, self.H), 0)
        if smooth:
            pts = catmull(pts, True, n)
        ImageDraw.Draw(m).polygon(self.P(pts), fill=255)
        return m

    def clipped(self, mask, draw_fn):
        """Run draw_fn(ImageDraw, pen) on a temp layer and composite through mask."""
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        draw_fn(d, self)
        a = ImageChops.multiply(layer.getchannel("A"), mask)
        layer.putalpha(a)
        self.img.alpha_composite(layer)

    def pattern(self, pts, kind, color, spacing=2.0, size=0.45, smooth=False, angle=0.0, color2=None):
        """Fill a shape with a folk pattern: dots, stripes, checks, zigzag, scales, floral, tiger, leopard, waves, chevron."""
        mask = self.mask_of(pts, smooth)
        bb = mask.getbbox()
        if not bb:
            return
        s = self.s
        sp = spacing * s
        r_ = rng("pat", kind, len(pts), round(spacing, 2))
        col = rgb(color)

        def draw(d, pen):
            x0, y0, x1, y1 = bb
            if kind == "dots":
                rr = size * s / 2
                j = 0
                y = y0 - sp
                while y < y1 + sp:
                    off = (sp / 2) if j % 2 else 0
                    x = x0 - sp + off
                    while x < x1 + sp:
                        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
                        x += sp
                    y += sp * 0.87
                    j += 1
            elif kind in ("stripes", "vstripes"):
                wpx = max(1, int(size * s))
                if kind == "stripes":
                    y = y0
                    while y < y1:
                        d.line([(x0, y), (x1, y)], fill=col, width=wpx)
                        y += sp
                else:
                    x = x0
                    while x < x1:
                        d.line([(x, y0), (x, y1)], fill=col, width=wpx)
                        x += sp
            elif kind == "checks":
                j = 0
                y = y0
                while y < y1:
                    x = x0 + (sp if j % 2 else 0)
                    while x < x1:
                        d.rectangle([x, y, x + sp, y + sp], fill=col)
                        x += 2 * sp
                    y += sp
                    j += 1
            elif kind in ("zigzag", "chevron"):
                wpx = max(1, int(size * s))
                y = y0
                while y < y1 + sp:
                    P = []
                    x = x0 - sp
                    k = 0
                    while x < x1 + sp:
                        P.append((x, y + (sp * 0.35 if k % 2 else -sp * 0.35)))
                        x += sp * 0.6
                        k += 1
                    d.line(P, fill=col, width=wpx, joint="curve")
                    y += sp
            elif kind == "scales":
                rr = sp * 0.55
                j = 0
                y = y0 - sp
                wpx = max(1, int(size * s * 0.6))
                while y < y1 + sp:
                    x = x0 - sp + (sp / 2 if j % 2 else 0)
                    while x < x1 + sp:
                        d.arc([x - rr, y - rr, x + rr, y + rr], 0, 180, fill=col, width=wpx)
                        x += sp
                    y += sp * 0.5
                    j += 1
            elif kind == "floral":
                rr = size * s / 2
                j = 0
                y = y0
                c2 = rgb(color2 or shade(color, 0.5))
                while y < y1 + sp:
                    x = x0 + (sp / 2 if j % 2 else 0)
                    while x < x1 + sp:
                        for a in range(0, 360, 90):
                            px = x + math.cos(math.radians(a + 45)) * rr * 1.3
                            py = y + math.sin(math.radians(a + 45)) * rr * 1.3
                            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col)
                        d.ellipse([x - rr * 0.7, y - rr * 0.7, x + rr * 0.7, y + rr * 0.7], fill=c2)
                        x += sp * 1.6
                    y += sp * 1.4
                    j += 1
            elif kind == "tiger":
                wpx = max(2, int(size * s))
                x = x0
                while x < x1:
                    xs = x + r_.uniform(-sp * 0.2, sp * 0.2)
                    P = [(xs + r_.uniform(-sp * .15, sp * .15), y0 + (y1 - y0) * f) for f in (0, .2, .4, .6)]
                    d.line(P, fill=col, width=wpx, joint="curve")
                    x += sp
            elif kind == "leopard":
                rr = size * s
                for _ in range(int((x1 - x0) * (y1 - y0) / (sp * sp)) + 1):
                    x, y = r_.uniform(x0, x1), r_.uniform(y0, y1)
                    d.ellipse([x - rr, y - rr * .8, x + rr, y + rr * .8], outline=col, width=max(1, int(rr * .4)))
            elif kind == "waves":
                wpx = max(1, int(size * s * 0.5))
                rr = sp * 0.5
                j = 0
                y = y0
                while y < y1 + sp:
                    x = x0 - sp + (rr if j % 2 else 0)
                    while x < x1 + sp:
                        d.arc([x - rr, y - rr, x + rr, y + rr], 180, 360, fill=col, width=wpx)
                        d.arc([x - rr * .55, y - rr * .55, x + rr * .55, y + rr * .55], 180, 360, fill=col, width=wpx)
                        x += sp
                    y += sp * 0.55
                    j += 1
            elif kind == "speckle":
                rr = max(1, size * s / 2)
                for _ in range(int((x1 - x0) * (y1 - y0) / (sp * sp) * 2) + 1):
                    x, y = r_.uniform(x0, x1), r_.uniform(y0, y1)
                    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)

        self.clipped(mask, draw)

    # -- finishing
    def finish(self, outline="ink", ow=0.32, inner=0.30, texture=0.9, seed=0, glow_rim=0.0, inner_r=0.9,
               bevel=0.0, rim=0.0) -> Sprite:
        """Down-sample + gouache texture + edge shading + cut-paper outline.

        inner/inner_r : darkening toward the cut edge (volume)  — strength / radius in units
        bevel         : directional shade on the lower-right edges (light from upper-left)
        rim           : light catching the upper-left edges (2.5D cut-out highlight)
        """
        img = self.img
        if outline is not None and ow > 0:
            a = img.getchannel("A")
            rad = ow * self.s
            bl = a.filter(ImageFilter.GaussianBlur(rad * 0.75))
            ring = bl.point(lambda v: 255 if v > 22 else int(v * 11.6))
            base = Image.new("RGBA", img.size, rgb(outline)[:3] + (0,))
            base.putalpha(ring)
            base.alpha_composite(img)
            img = base
        W, H = img.size
        w, h = max(1, round(W / self.ss)), max(1, round(H / self.ss))
        img = img.resize((w, h), Image.LANCZOS)
        arr = np.asarray(img, np.float32).copy()
        alpha = arr[..., 3] / 255.0
        if texture > 0:
            g = tile_to(grain_tile(256, 7 + seed % 5), w, h)
            arr[..., :3] *= (1 + (g[..., None] - 1) * texture * 1.6)
        a8 = Image.fromarray((alpha * 255).astype(np.uint8), "L")
        if inner > 0:
            r = max(1.0, inner_r * self.ppu)
            bl = np.asarray(a8.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0
            edge = np.clip((alpha - bl) * 2.2, 0, 1)
            arr[..., :3] *= (1 - inner * edge[..., None])
            # soft top-left light, like a lamp above the stage
            yy = np.linspace(1, 0, h, dtype=np.float32)[:, None]
            arr[..., :3] *= (0.94 + 0.10 * yy[..., None])
        if bevel > 0 or rim > 0:
            sh = max(1, int(round(0.7 * self.ppu)))
            soft = max(1.0, 0.8 * self.ppu)

            def shifted(dx, dy):
                m = np.zeros_like(alpha)
                ys, ye = max(0, dy), h + min(0, dy)
                xs, xe = max(0, dx), w + min(0, dx)
                m[ys - dy:ye - dy, xs - dx:xe - dx] = alpha[ys:ye, xs:xe]
                return np.asarray(Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(soft)),
                                  np.float32) / 255.0
            if bevel > 0:     # p near the lower-right edge  <=> alpha(p + s) is low
                dark = alpha * (1 - shifted(sh, sh))
                arr[..., :3] *= (1 - bevel * np.clip(dark * 1.6, 0, 1)[..., None])
            if rim > 0:       # p near the upper-left edge  <=> alpha(p - s) is low
                lit = alpha * (1 - shifted(-sh, -sh))
                arr[..., :3] += rim * 255 * np.clip(lit * 1.6, 0, 1)[..., None] * np.array([1.0, 0.94, 0.8])
        arr[..., :3] = np.clip(arr[..., :3], 0, 255)
        out = Image.fromarray(arr.astype(np.uint8), "RGBA")
        px, py = -self.x0 * self.ppu, -self.y0 * self.ppu
        return Sprite(out, px, py)


# finishing presets: puppets are thicker-lined, bevelled cut-outs that read as 2.5D
CHAR_STYLE = dict(outline="#170d07", ow=0.58, inner=0.34, inner_r=1.5, bevel=0.2, rim=0.13, texture=0.8)
ITEM_STYLE = dict(outline="#170d07", ow=0.42, inner=0.26, inner_r=0.9, bevel=0.16, rim=0.12, texture=0.6)


# =========================================================================== compositing

def affine_paste(dst: Image.Image, spr: Sprite, x, y, ang=0.0, sx=1.0, sy=None, alpha=1.0,
                 resample=Image.BICUBIC):
    """Paste sprite so its pivot lands on (x,y), rotated `ang` degrees (clockwise
    positive in screen space), scaled (sx, sy). Negative sx mirrors."""
    sy = sx if sy is None else sy
    if abs(sx) < 1e-4 or abs(sy) < 1e-4:
        return
    w, h = spr.img.size
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    # forward: p' = R * S * (p - pivot) + (x, y)
    corners = []
    for (u, v) in ((0, 0), (w, 0), (0, h), (w, h)):
        du, dv = (u - spr.px) * sx, (v - spr.py) * sy
        corners.append((x + c * du - s * dv, y + s * du + c * dv))
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    X0, Y0 = int(math.floor(min(xs))) - 1, int(math.floor(min(ys))) - 1
    X1, Y1 = int(math.ceil(max(xs))) + 1, int(math.ceil(max(ys))) + 1
    DW, DH = dst.size
    cx0, cy0, cx1, cy1 = max(0, X0), max(0, Y0), min(DW, X1), min(DH, Y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    # inverse: p = S^-1 R^-1 (p' - t) + pivot ; p' = (cx0 + i, cy0 + j)
    ia, ib = c / sx, s / sx
    ic, id_ = -s / sy, c / sy
    tx, ty = cx0 - x, cy0 - y
    coeffs = (ia, ib, ia * tx + ib * ty + spr.px,
              ic, id_, ic * tx + id_ * ty + spr.py)
    patch = spr.img.transform((cx1 - cx0, cy1 - cy0), Image.AFFINE, coeffs, resample=resample)
    if alpha < 0.999:
        patch.putalpha(patch.getchannel("A").point(lambda v: int(v * alpha)))
    dst.alpha_composite(patch, (cx0, cy0))


def add_light(dst: Image.Image, light: Image.Image, pos=(0, 0)):
    """Additive (screen-like) light: light RGBA, alpha used as intensity."""
    lw, lh = light.size
    x, y = int(pos[0]), int(pos[1])
    box = (max(0, x), max(0, y), min(dst.size[0], x + lw), min(dst.size[1], y + lh))
    if box[2] <= box[0] or box[3] <= box[1]:
        return
    region = dst.crop(box)
    lcrop = light.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
    a = lcrop.getchannel("A")
    lrgb = Image.merge("RGB", [ImageChops.multiply(ch, a) for ch in lcrop.split()[:3]])
    out = ImageChops.screen(region.convert("RGB"), lrgb)
    out = out.convert("RGBA")
    out.putalpha(region.getchannel("A"))
    dst.paste(out, box[:2])


def drop_shadow_and_glow(canvas: Image.Image, shadow=(10, 8, 0.45, 9), glow=None):
    """Return a new image with soft shadow (dx,dy,opacity,radius) and optional
    rim glow (colour, opacity, radius) behind the canvas content."""
    a = canvas.getchannel("A")
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if glow:
        col, op, rad = glow
        g = blur_alpha_fast(a, rad).point(lambda v: int(min(255, v * op * 1.6)))
        gl = Image.new("RGBA", canvas.size, rgb(col)[:3] + (0,))
        gl.putalpha(g)
        out.alpha_composite(gl)
    if shadow:
        dx, dy, op, rad = shadow
        sh = blur_alpha_fast(a, rad).point(lambda v: int(v * op))
        sl = Image.new("RGBA", canvas.size, (20, 10, 4, 0))
        sl.putalpha(sh)
        out.alpha_composite(sl, (int(dx), int(dy)))
    out.alpha_composite(canvas)
    return out
