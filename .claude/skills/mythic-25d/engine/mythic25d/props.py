"""Scenery props, painted as cut-paper theatre flats.

Units: 1u = 1% of frame height.  Every builder draws on a Pen whose origin is
the prop's anchor (bottom-centre for standing props, string-top for hanging
props).  `build_prop(name, ppu, **params)` returns a finished Sprite (cached).
"""
from __future__ import annotations

import math
import pickle

from .gfx import Pen, arc_pts, bezier, catmull, limb, rot
from .util import code_version, CACHE_DIR, mix, rgb, rng, shade, stable_hash

PROP_VERSION = code_version("props", "gfx")
INK = "ink"


# =========================================================================== sky props (hang on strings)

def cloud(p, color="#e8dcc4", kind="puffy", seed=0, w=24.0):
    r = rng("cloud", seed)
    line = shade(color, -0.3)
    if kind == "curl":   # the swirl-cloud of Indian miniature painting
        pts = catmull([(-w * 0.5, 0), (-w * 0.2, -2.4), (w * 0.15, -1.0), (w * 0.38, -3.2), (w * 0.44, -6.0),
                       (w * 0.3, -7.2), (w * 0.2, -5.6)], False, 8)
        for i in range(len(pts) - 1):
            p.poly(limb(pts[i], pts[i + 1], 3.2 - 1.6 * i / len(pts), 3.0 - 1.6 * i / len(pts)), fill=color)
        p.line(pts, line, 0.3)
        return (-w * 0.6, -10, w * 0.6, 4)
    lobes = [(-w * 0.32, -3.0, 5.2), (-w * 0.12, -6.4, 6.4), (w * 0.1, -6.8, 6.0), (w * 0.3, -3.6, 5.0),
             (0, -1.6, 6.0), (-w * 0.42, -0.4, 3.4), (w * 0.42, -0.6, 3.2)]
    for (x, y, rr) in lobes:
        p.circle(x, y, rr, fill=color)
    p.poly([(-w * 0.48, 0.6), (w * 0.48, 0.6), (w * 0.4, -2.0), (-w * 0.4, -2.0)], fill=color)
    # scalloped inner line work + spiral curls (Kalamkari cloud)
    for (x, y, rr) in lobes[:4]:
        p.arc(x, y + rr * 0.15, rr * 0.62, rr * 0.55, 200, 340, line, 0.28)
        p.line(arc_pts(x + rr * 0.1, y + rr * 0.2, rr * 0.28, rr * 0.26, 180, 470, 16), line, 0.22)
    p.line([(-w * 0.46, 0.6), (w * 0.46, 0.6)], line, 0.3)
    for k in range(5):
        x = -w * 0.36 + k * w * 0.18
        p.circle(x, 1.6, 0.5, fill=shade(color, -0.15))
    return (-w * 0.6, -14, w * 0.6, 4)


def sun(p, color="#e8a63a", rays="#d9822a", R=6.5, face=False):
    for k in range(16):
        a = math.radians(k * 22.5)
        p.poly([(math.cos(a - 0.17) * R, math.sin(a - 0.17) * R),
                (math.cos(a) * (R + 3.4), math.sin(a) * (R + 3.4)),
                (math.cos(a + 0.17) * R, math.sin(a + 0.17) * R)], fill=rays)
    p.circle(0, 0, R, fill=color)
    p.circle(0, 0, R * 0.78, outline=shade(color, -0.3), w=0.28)
    p.circle(0, 0, R * 0.55, fill=shade(color, 0.2))
    for k in range(12):
        a = math.radians(k * 30)
        p.circle(math.cos(a) * R * 0.66, math.sin(a) * R * 0.66, 0.42, fill=shade(color, -0.35))
    for k in range(8):
        a = math.radians(k * 45 + 22)
        p.poly([(0, 0), (math.cos(a - 0.2) * R * 0.5, math.sin(a - 0.2) * R * 0.5),
                (math.cos(a + 0.2) * R * 0.5, math.sin(a + 0.2) * R * 0.5)], fill=shade(color, -0.12))
    p.circle(0, 0, R * 0.16, fill="vermilion")
    return (-R - 4, -R - 4, R + 4, R + 4)


def moon(p, color="#efe6cf", R=4.6, full=False):
    if full:
        p.circle(0, 0, R, fill=color)
        for (x, y, rr) in ((-1.2, -1.0, 0.9), (1.4, 0.8, 0.7), (0.2, 1.8, 0.5)):
            p.circle(x, y, rr, fill=shade(color, -0.1))
    else:
        p.poly(arc_pts(0, 0, R, R, 60, 300, 24) + arc_pts(1.6, -0.2, R * 0.82, R * 0.86, 300, 60, 24)[::-1],
               fill=color)
    return (-R - 1, -R - 1, R + 1, R + 1)


def star(p, color="#f2e2b0", R=1.6):
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        rr = R if k % 2 == 0 else R * 0.42
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    p.poly(pts, fill=color)
    return (-R - 0.5, -R - 0.5, R + 0.5, R + 0.5)


# =========================================================================== trees & plants

def tree(p, kind="kalamkari", h=48.0, seed=0, leaf="#4f7d3a", fruit="vermilion", trunk="#6a4428", night=False):
    r = rng("tree", kind, seed)
    lc = shade(leaf, -0.35)
    if night:
        leaf, lc, trunk = "#1e1a22", "#120e14", "#141016"
    if kind == "banana":
        p.poly(limb((0, 0), (0.6, -h * 0.55), 3.2, 2.4), fill=trunk if not night else trunk)
        p.pattern(limb((0, 0), (0.6, -h * 0.55), 3.2, 2.4), "stripes", shade(trunk, -0.2), 2.0, 0.3)
        top = (0.6, -h * 0.55)
        for k in range(9):
            a = -90 + (k - 4) * 26 + r.uniform(-8, 8)
            L = h * r.uniform(0.32, 0.46)
            tip = (top[0] + math.cos(math.radians(a)) * L, top[1] + math.sin(math.radians(a)) * L * 0.9)
            mid = ((top[0] + tip[0]) / 2, (top[1] + tip[1]) / 2 - 2)
            nx, ny = -(tip[1] - top[1]) / L, (tip[0] - top[0]) / L
            leafpts = [top, (mid[0] + nx * 3.2, mid[1] + ny * 3.2), tip, (mid[0] - nx * 3.0, mid[1] - ny * 3.0)]
            p.poly(leafpts, fill=leaf if k % 2 else shade(leaf, 0.08), smooth=True, n=8)
            p.line([top, mid, tip], lc, 0.32, smooth=True)
            if not night:
                p.pattern(leafpts, "dots", shade(leaf, 0.45), 1.8, 0.3, smooth=True)
            for j in range(4):
                f = 0.3 + j * 0.17
                bx, by = top[0] + (tip[0] - top[0]) * f, top[1] + (tip[1] - top[1]) * f
                p.line([(bx, by), (bx + nx * 2.6, by + ny * 2.6 + 0.8)], lc, 0.16)
        if not night:
            p.poly([(0.8, -h * 0.5), (2.6, -h * 0.4), (1.8, -h * 0.32), (0.2, -h * 0.42)], fill="#7a2a3a", smooth=True)
        return (-h * 0.55, -h * 1.05, h * 0.55, 1)
    if kind == "palm":
        pts = catmull([(0, 0), (1.6, -h * 0.4), (2.4, -h * 0.75)], False, 10)
        for i in range(len(pts) - 1):
            p.poly(limb(pts[i], pts[i + 1], 2.6, 2.2), fill=trunk)
        for i in range(0, len(pts), 2):
            x, y = pts[i]
            p.line([(x - 1.2, y), (x + 1.2, y + 0.4)], shade(trunk, -0.3), 0.2)
        top = pts[-1]
        for k in range(10):
            a = -90 + (k - 4.5) * 30
            tip = (top[0] + math.cos(math.radians(a)) * h * 0.32, top[1] + math.sin(math.radians(a)) * h * 0.2 + h * 0.06)
            ctrl = (top[0] + math.cos(math.radians(a)) * h * 0.2, top[1] - h * 0.08)
            path = bezier(top, ctrl, ctrl, tip, 10)
            for i in range(len(path) - 1):
                p.poly(limb(path[i], path[i + 1], 2.0 * (1 - i / 12) + 0.4, 2.0 * (1 - (i + 1) / 12) + 0.4), fill=leaf)
            p.line(path, lc, 0.18)
        for k in range(3):
            p.circle(top[0] - 1 + k * 1.2, top[1] + 1.4, 1.0, fill="#7a5a2a")
        return (-h * 0.4, -h * 1.1, h * 0.45, 1)
    if kind == "pine":
        p.poly(limb((0, 0), (0, -h * 0.3), 2.0, 1.6), fill=trunk)
        for k in range(5):
            y = -h * 0.2 - k * h * 0.15
            w = h * (0.26 - k * 0.04)
            p.poly([(-w, y), (0, y - h * 0.24), (w, y)], fill=shade(leaf, -0.05 * k))
            p.line([(-w * 0.7, y - 0.8), (0, y - h * 0.18), (w * 0.7, y - 0.8)], lc, 0.2)
        return (-h * 0.3, -h * 1.05, h * 0.3, 1)
    if kind == "bamboo":
        for k in range(5):
            x = (k - 2) * 2.2 + r.uniform(-0.6, 0.6)
            hh = h * r.uniform(0.8, 1.0)
            p.poly(limb((x, 0), (x + r.uniform(-2, 2), -hh), 1.2, 1.0), fill="#8aa04a")
            for j in range(1, 6):
                yy = -hh * j / 6
                p.line([(x - 0.8 + (j * 0.05), yy), (x + 0.8, yy)], "#4a6a2a", 0.3)
                p.poly([(x, yy), (x + 4.0 * (1 if j % 2 else -1), yy - 1.6), (x + 2.0 * (1 if j % 2 else -1), yy + 0.4)],
                       fill=leaf)
        return (-h * 0.25, -h * 1.05, h * 0.25, 1)
    # ---- canopy trees: kalamkari / mango / peepal / ashoka / kadamba / flowering / banyan / night
    tw = h * 0.07
    p.poly([(-tw * 1.6, 0), (-tw * 0.7, -h * 0.25), (-tw * 0.6, -h * 0.5), (tw * 0.6, -h * 0.5), (tw * 0.7, -h * 0.25),
            (tw * 1.6, 0)], fill=trunk, smooth=False)
    for k in range(4):
        p.line([(-tw * 0.5 + k * tw * 0.35, -1), (-tw * 0.4 + k * tw * 0.3, -h * 0.45)], shade(trunk, -0.3), 0.18)
    # branches
    branches = []
    for k in range(5):
        a = -90 + (k - 2) * 30 + r.uniform(-8, 8)
        L = h * r.uniform(0.22, 0.32)
        sx, sy = 0, -h * r.uniform(0.38, 0.5)
        ex, ey = sx + math.cos(math.radians(a)) * L, sy + math.sin(math.radians(a)) * L
        p.poly(limb((sx, sy), (ex, ey), tw * 0.9, tw * 0.35), fill=trunk)
        branches.append((ex, ey))
    if kind == "banyan":
        for k in range(7):
            x = r.uniform(-h * 0.35, h * 0.35)
            p.line([(x, -h * 0.55), (x + r.uniform(-1, 1), -1)], shade(trunk, 0.1), 0.35)
    cx, cy = 0, -h * 0.72
    R = h * 0.36
    clusters = [(cx + r.uniform(-R * 0.9, R * 0.9), cy + r.uniform(-R * 0.55, R * 0.45), r.uniform(R * 0.28, R * 0.42))
                for _ in range(9)] + [(bx, by - 2, R * 0.3) for bx, by in branches]
    clusters.sort(key=lambda c: c[1])
    fc = {"kalamkari": fruit, "mango": "#e8a03a", "ashoka": "#d84a2a", "kadamba": "#f0a830", "flowering": "#f2a2b8",
          "peepal": None, "banyan": None, "night": "#c8321f"}.get(kind, fruit)
    for i, (x, y, rr) in enumerate(clusters):
        col = leaf if i % 3 else shade(leaf, 0.07)
        if kind == "flowering":
            col = mix(leaf, "#e8a0b0", 0.35) if i % 2 else leaf
        p.circle(x, y, rr, fill=col)
        if kind == "peepal":
            for j in range(6):
                a = r.uniform(0, 2 * math.pi)
                lx, ly = x + math.cos(a) * rr * 0.6, y + math.sin(a) * rr * 0.6
                p.poly([(lx, ly - 1.2), (lx + 1.0, ly), (lx, ly + 1.8), (lx - 1.0, ly)], fill=shade(col, 0.2), smooth=True)
        else:
            p.pattern(arc_pts(x, y, rr * 0.92, rr * 0.92, 0, 360, 24), "dots", shade(col, 0.42 if not night else 0.1),
                      1.5, 0.32)
        p.arc(x, y, rr * 0.92, rr * 0.92, 200, 330, lc, 0.3)
        if fc and r.random() < 0.85:
            for j in range(r.randint(1, 3)):
                a = r.uniform(0, 2 * math.pi)
                p.circle(x + math.cos(a) * rr * 0.55, y + math.sin(a) * rr * 0.55, 1.0 if kind != "kadamba" else 1.4,
                         fill=fc)
    return (-h * 0.62, -h * 1.15, h * 0.62, 1)


def bush(p, color="#3f6a34", w=14.0, seed=0, flowers=None):
    r = rng("bush", seed)
    for k in range(7):
        x = r.uniform(-w * 0.4, w * 0.4)
        rr = r.uniform(w * 0.16, w * 0.26)
        p.circle(x, -rr * 0.8, rr, fill=color if k % 2 else shade(color, 0.08))
        p.pattern(arc_pts(x, -rr * 0.8, rr * 0.9, rr * 0.9, 0, 360, 16), "dots", shade(color, 0.4), 1.4, 0.3)
        if flowers:
            p.circle(x + rr * 0.3, -rr * 1.1, 0.8, fill=flowers)
    return (-w * 0.75, -w * 0.7, w * 0.75, 1)


def lotus(p, color="#ea8fa3", leaf="#3f7a4a", n=3, seed=0):
    r = rng("lotus", seed)
    for k in range(n + 1):
        x = (k - n / 2) * 6 + r.uniform(-1, 1)
        p.ellipse(x, 0, 3.2, 0.9, fill=leaf)
        p.line([(x, 0), (x + 2.6, -0.3)], shade(leaf, -0.3), 0.15)
    for k in range(n):
        x = (k - (n - 1) / 2) * 6.4
        for j, a in enumerate((-50, -25, 0, 25, 50)):
            pet = rot([(x, -1.0), (x - 0.9, -2.6), (x, -4.6), (x + 0.9, -2.6)], a, x, -1.0)
            p.poly(pet, fill=color if j % 2 else shade(color, 0.2), smooth=True)
    return (-n * 4 - 4, -6, n * 4 + 4, 1.5)


def grass(p, color="#5a7a34", w=10.0, seed=0):
    r = rng("grass", seed)
    for k in range(14):
        x = r.uniform(-w / 2, w / 2)
        hh = r.uniform(2, 4.5)
        p.poly([(x - 0.4, 0), (x + r.uniform(-1.4, 1.4), -hh), (x + 0.4, 0)], fill=color if k % 2 else shade(color, -0.15))
    return (-w / 2 - 2, -5, w / 2 + 2, 0.5)


def rock(p, color="#7a6e62", w=16.0, h=7.0, seed=0):
    r = rng("rock", seed)
    pts = [(-w / 2, 0), (-w * 0.45, -h * 0.6), (-w * 0.2, -h), (w * 0.15, -h * 0.9), (w * 0.42, -h * 0.55), (w / 2, 0)]
    pts = [(x + r.uniform(-0.6, 0.6), y + r.uniform(-0.4, 0.4)) for x, y in pts]
    p.poly(pts, fill=color, smooth=True)
    p.pattern(pts, "speckle", shade(color, -0.2), 1.2, 0.3, smooth=True)
    p.line([(-w * 0.2, -h * 0.85), (-w * 0.05, -h * 0.3), (w * 0.2, -h * 0.5)], shade(color, -0.35), 0.25)
    return (-w / 2 - 1, -h - 1, w / 2 + 1, 0.5)


def mountains(p, color="#6a5a6a", w=200.0, h=34.0, seed=0, snow=False, peaks=6, style="soft"):
    r = rng("mtn", seed)
    ridge = [(-w / 2, -h * 0.25)]
    for k in range(peaks):
        x0 = -w / 2 + (k + 0.15) * w / peaks
        px = x0 + r.uniform(0.15, 0.7) * w / peaks
        ph = h * r.uniform(0.55, 1.0)
        ridge += [(x0, -h * r.uniform(0.15, 0.4)), (px, -ph)]
    ridge += [(w / 2, -h * 0.3)]
    top = catmull(ridge, False, 6) if style == "soft" else ridge
    top = [(x, min(y, 0)) for x, y in top]
    p.poly(top + [(w / 2, 0), (-w / 2, 0)], fill=color)
    # second, lighter ridge for painted depth
    p.poly([(x, y * 0.55) for x, y in top] + [(w / 2, 0), (-w / 2, 0)], fill=shade(color, 0.08))
    if snow:
        for i in range(2, len(ridge) - 1, 2):
            x, y = ridge[i]
            if y < -h * 0.6:
                p.poly([(x - 4.0, y + 4.6), (x, y - 0.1), (x + 4.2, y + 4.8), (x + 1.6, y + 3.6), (x, y + 5.0),
                        (x - 1.6, y + 3.4)], fill="#f2f0e8")
    for i in range(2, len(ridge) - 1, 2):
        x, y = ridge[i]
        p.line([(x, y + 1), (x - 3.0, y + h * 0.4)], shade(color, -0.18), 0.4)
    return (-w / 2, -h - 2, w / 2, 1)


# =========================================================================== architecture

def cusped_arch(p, x, base, w, h, fill, line, lobes=5):
    """Mughal/Rajput multi-foil arch outline points (opening)."""
    pts = [(x - w / 2, base), (x - w / 2, base - h * 0.62)]
    for k in range(lobes):
        a0 = 180 + k * 180 / lobes
        cx = x + math.cos(math.radians(a0 + 90 / lobes)) * w * 0.42
        cy = base - h * 0.62 + math.sin(math.radians(a0 + 90 / lobes)) * h * 0.36
        pts += arc_pts(cx, cy, w * 0.12, w * 0.12, a0 - 30, a0 + 150, 6)
    pts += [(x, base - h * 1.02)]
    pts = [pt for pt in pts]
    pts += [(x + w / 2, base - h * 0.62), (x + w / 2, base)]
    p.poly(pts, fill=fill)
    p.line(pts, line, 0.4)
    return pts


def palace(p, wall="#d8b47a", trim="gold", accent="vermilion", window="#2b3a5a", w=180.0, h=62.0, seed=0, bays=5,
           curtains=True, garlands=True, interior=False):
    r = rng("palace", seed)
    line = shade(wall, -0.45)
    p.poly([(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)], fill=wall)
    p.pattern([(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)], "speckle", shade(wall, -0.08), 2.0, 0.4)
    # cornice
    p.poly([(-w / 2 - 2, -h), (w / 2 + 2, -h), (w / 2 + 2, -h - 3.6), (-w / 2 - 2, -h - 3.6)], fill=shade(wall, -0.12))
    p.pattern([(-w / 2 - 2, -h), (w / 2 + 2, -h), (w / 2 + 2, -h - 3.6), (-w / 2 - 2, -h - 3.6)], "checks", trim, 1.2)
    bw = w / bays
    for k in range(bays):
        x = -w / 2 + bw * (k + 0.5)
        ah = h * 0.78
        aw = bw * 0.62
        cusped_arch(p, x, -2, aw, ah, window, line)
        if interior:
            p.pattern([(x - aw / 2, -2), (x + aw / 2, -2), (x + aw / 2, -ah * 0.6), (x - aw / 2, -ah * 0.6)], "vstripes",
                      shade(window, 0.15), 1.6, 0.3)
        else:  # jali lattice
            p.pattern([(x - aw / 2 + 1, -2), (x + aw / 2 - 1, -2), (x + aw / 2 - 1, -ah * 0.62), (x - aw / 2 + 1, -ah * 0.62)],
                      "vstripes", shade(window, 0.5), 2.2, 0.3)
            p.pattern([(x - aw / 2 + 1, -2), (x + aw / 2 - 1, -2), (x + aw / 2 - 1, -ah * 0.62), (x - aw / 2 + 1, -ah * 0.62)],
                      "stripes", shade(window, 0.5), 3.2, 0.25)
        # arch frame with dotted trim
        p.line(arc_pts(x, -ah * 0.62 - 2, aw * 0.6, ah * 0.46, 180, 360, 20), trim, 0.9)
        p.pattern(arc_pts(x, -ah * 0.62 - 2, aw * 0.62, ah * 0.48, 180, 360, 20) + [(x + aw * 0.6, -ah * 0.62),
                  (x - aw * 0.6, -ah * 0.62)], "dots", accent, 1.4, 0.3)
        if curtains and k % 2 == 0:
            p.poly([(x - aw / 2, -ah * 0.8), (x - aw * 0.05, -ah * 0.75), (x - aw * 0.3, -2), (x - aw / 2, -2)],
                   fill=accent, smooth=True)
            p.pattern([(x - aw / 2, -ah * 0.8), (x - aw * 0.05, -ah * 0.75), (x - aw * 0.3, -2), (x - aw / 2, -2)],
                      "vstripes", shade(accent, -0.2), 1.2, 0.3)
    # pillars between bays
    for k in range(bays + 1):
        x = -w / 2 + bw * k
        p.poly([(x - 2.2, 0), (x + 2.2, 0), (x + 1.8, -h), (x - 1.8, -h)], fill=shade(wall, 0.12))
        for y in (-h * 0.15, -h * 0.5, -h * 0.85):
            p.poly([(x - 2.8, y - 1.2), (x + 2.8, y - 1.2), (x + 2.8, y + 1.2), (x - 2.8, y + 1.2)], fill=trim)
        p.line([(x - 0.6, -2), (x - 0.6, -h + 2)], shade(wall, -0.2), 0.25)
    if garlands:
        for k in range(bays):
            x0 = -w / 2 + bw * k
            pts = arc_pts(x0 + bw / 2, -h + 2, bw / 2, 5.0, 0, 180, 14)
            for (gx, gy) in pts[::1]:
                p.circle(gx, gy, 0.85, fill="#f09a2a" if r.random() < 0.6 else "#f2c94a")
            for j in range(3):
                gx = x0 + bw * (0.25 + j * 0.25)
                p.line([(gx, -h + 3), (gx, -h + 9)], "#f09a2a", 0.6)
    return (-w / 2 - 3, -h - 5, w / 2 + 3, 1)


def pillar(p, h=60.0, color="#e6d8bc", trim="gold"):
    p.poly([(-3.4, 0), (3.4, 0), (2.6, -h), (-2.6, -h)], fill=color)
    for k in range(5):
        x = -2.0 + k
        p.line([(x, -3), (x * 0.8, -h + 4)], shade(color, -0.25), 0.25)
    for y, ww in ((0, 4.6), (-h, 4.0), (-h * 0.5, 3.4)):
        p.poly([(-ww, y - 1.6), (ww, y - 1.6), (ww, y + 1.0), (-ww, y + 1.0)], fill=trim)
    p.poly([(-4.6, -h - 1.6), (4.6, -h - 1.6), (5.4, -h - 4.0), (-5.4, -h - 4.0)], fill=shade(trim, -0.1))
    return (-6, -h - 5, 6, 1.5)


def temple(p, color="#d8a85a", h=70.0, flag="vermilion", seed=0):
    w = h * 0.42
    # garbhagriha base
    p.poly([(-w * 0.62, 0), (w * 0.62, 0), (w * 0.62, -h * 0.3), (-w * 0.62, -h * 0.3)], fill=shade(color, -0.05))
    cusped_arch(p, 0, 0, w * 0.4, h * 0.24, "#2a1a14", shade(color, -0.45))
    # shikhara: stacked curved tiers
    tiers = 7
    for k in range(tiers):
        y0 = -h * 0.3 - k * h * 0.075
        a = w * 0.55 * (1 - k / (tiers + 1.5))
        b = w * 0.55 * (1 - (k + 1) / (tiers + 1.5))
        p.poly([(-a, y0), (-b * 1.05, y0 - h * 0.04), (-b, y0 - h * 0.075), (b, y0 - h * 0.075), (b * 1.05, y0 - h * 0.04), (a, y0)],
               fill=color if k % 2 == 0 else shade(color, 0.1))
        p.line([(-a, y0), (a, y0)], shade(color, -0.4), 0.3)
    top = -h * 0.3 - tiers * h * 0.075
    p.ellipse(0, top - 1.6, w * 0.22, 1.8, fill=shade(color, 0.05))
    p.poly([(-1.4, top - 3.0), (0, top - 8.0), (1.4, top - 3.0)], fill="gold")
    p.circle(0, top - 3.4, 1.4, fill="gold")
    p.line([(0, top - 8), (0, top - 15)], "#6a4428", 0.3)
    p.poly([(0, top - 15), (5.0, top - 13.6), (0, top - 12.2)], fill=flag)
    return (-w * 0.7, top - 16, w * 0.7, 1)


def fort(p, color="#b8864a", w=200.0, h=34.0, seed=0, towers=5, gold=False):
    r = rng("fort", seed)
    c = "#d8a838" if gold else color
    p.poly([(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)], fill=c)
    p.pattern([(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)], "checks", shade(c, -0.08), 3.0)
    for k in range(int(w / 6)):
        x = -w / 2 + k * 6
        p.poly([(x, -h), (x + 3.4, -h), (x + 3.4, -h - 3.0), (x, -h - 3.0)], fill=c)
    for k in range(towers):
        x = -w / 2 + (k + 0.5) * w / towers + r.uniform(-4, 4)
        th = h * r.uniform(1.3, 1.7)
        p.poly([(x - 6, 0), (x + 6, 0), (x + 5, -th), (x - 5, -th)], fill=shade(c, 0.08))
        p.ellipse(x, -th, 6.4, 5.2, fill=shade(c, 0.15))
        p.poly([(x - 0.8, -th - 4.6), (x, -th - 9), (x + 0.8, -th - 4.6)], fill="gold")
        for y in (-th * 0.4, -th * 0.7):
            cusped_arch(p, x, y, 4.0, 6.0, "#2a1a14", shade(c, -0.4), lobes=3)
    gx = 0
    cusped_arch(p, gx, 0, 16, h * 0.8, "#2a1a14", shade(c, -0.45))
    return (-w / 2 - 2, -h * 1.8 - 10, w / 2 + 2, 1)


def city(p, color="#d8cfc0", w=200.0, h=40.0, seed=0, n=14):
    """Distant skyline of temple spires and domes (like the reference's white city)."""
    r = rng("city", seed)
    for k in range(n):
        x = -w / 2 + (k + 0.5) * w / n + r.uniform(-3, 3)
        hh = h * r.uniform(0.35, 1.0)
        ww = w / n * r.uniform(0.5, 0.9)
        c = shade(color, r.uniform(-0.1, 0.08))
        if r.random() < 0.6:
            p.poly([(x - ww / 2, 0), (x + ww / 2, 0), (x + ww * 0.35, -hh * 0.6), (x, -hh), (x - ww * 0.35, -hh * 0.6)],
                   fill=c, smooth=False)
            for j in range(4):
                y = -hh * 0.15 * (j + 1)
                p.line([(x - ww * 0.4, y), (x + ww * 0.4, y)], shade(c, -0.15), 0.25)
        else:
            p.poly([(x - ww / 2, 0), (x + ww / 2, 0), (x + ww / 2, -hh * 0.6), (x - ww / 2, -hh * 0.6)], fill=c)
            p.ellipse(x, -hh * 0.6, ww * 0.42, hh * 0.25, fill=c)
        p.line([(x, -hh), (x, -hh - 3)], shade(c, -0.3), 0.2)
    return (-w / 2 - 2, -h - 4, w / 2 + 2, 1)


def hut(p, wall="#c89a5a", roof="#d8b04a", seed=0):
    p.poly([(-9, 0), (9, 0), (9, -11), (-9, -11)], fill=wall)
    p.pattern([(-9, 0), (9, 0), (9, -11), (-9, -11)], "vstripes", shade(wall, -0.15), 1.6, 0.3)
    p.poly([(-2.6, 0), (2.6, 0), (2.6, -7.2), (-2.6, -7.2)], fill="#2a1a10")
    roof_pts = [(-13, -9.6), (0, -24), (13, -9.6), (10, -10.6), (-10, -10.6)]
    p.poly(roof_pts, fill=roof, smooth=False)
    for k in range(9):
        x = -12 + k * 3
        p.line([(x, -10), (x * 0.25, -22)], shade(roof, -0.25), 0.25)
    p.pattern(roof_pts, "zigzag", shade(roof, -0.2), 2.4, 0.25)
    return (-14, -25, 14, 1)


def tent(p, c1="#e0a83a", c2="vermilion", flag="saffron", w=26.0, h=22.0):
    pts = [(-w / 2, 0), (0, -h), (w / 2, 0)]
    p.poly(pts, fill=c1)
    n = 6
    for k in range(n):
        if k % 2:
            p.poly([(-w / 2 + k * w / n, 0), (0, -h), (-w / 2 + (k + 1) * w / n, 0)], fill=c2)
    p.poly([(-2.6, 0), (0, -h * 0.4), (2.6, 0)], fill="#2a1a10")
    p.line([(0, -h), (0, -h - 6)], "#6a4428", 0.3)
    p.poly([(0, -h - 6), (4.4, -h - 4.8), (0, -h - 3.6)], fill=flag)
    return (-w / 2 - 1, -h - 7, w / 2 + 1, 1)


def flagpole(p, color="saffron", h=26.0, emblem=None, kind="pennant"):
    p.poly(limb((0, 0), (0, -h), 0.6, 0.5), fill="#6a4428")
    p.circle(0, -h - 0.6, 0.8, fill="gold")
    if kind == "banner":
        pts = [(0.4, -h + 0.6), (12, -h + 0.2), (13, -h + 5.6), (12, -h + 11), (0.4, -h + 10.6)]
        p.poly(pts, fill=color)
        if emblem == "hanuman":
            p.circle(6.0, -h + 4.4, 1.6, fill="#7a3a1a")
            p.poly([(4.4, -h + 9.6), (6.0, -h + 5.4), (7.6, -h + 9.6)], fill="#7a3a1a")
        elif emblem:
            p.circle(6.0, -h + 5.6, 2.2, fill=emblem)
    else:
        p.poly([(0.4, -h + 0.4), (7.0, -h + 2.2), (0.4, -h + 4.6)], fill=color)
    return (-1, -h - 2, 14, 1)


def deepstambh(p, h=22.0, color="gold", lit=True):
    """Tall brass lamp stand (samai) — flames animated separately."""
    c = color
    p.poly([(-4.2, 0), (4.2, 0), (3.0, -1.6), (-3.0, -1.6)], fill=shade(c, -0.1))
    p.poly(limb((0, -1.6), (0, -h), 1.4, 1.0), fill=c)
    for y in (-h * 0.3, -h * 0.55, -h * 0.8):
        p.ellipse(0, y, 1.8, 0.7, fill=shade(c, 0.1))
    p.poly([(-4.6, -h), (4.6, -h), (3.4, -h - 1.6), (-3.4, -h - 1.6)], fill=c)
    p.line([(-4.6, -h), (4.6, -h)], shade(c, -0.35), 0.3)
    return (-5.4, -h - 3, 5.4, 1)


def diya_prop(p):
    p.poly([(-1.8, 0), (1.8, 0), (2.4, -1.2), (-2.4, -1.2)], fill="#b8742c", smooth=True)
    return (-3, -2, 3, 0.6)


def yagya_kund(p, color="#a8744a"):
    for k in range(3):
        w = 16 - k * 3.4
        y = -k * 2.4
        p.poly([(-w, y), (w, y), (w - 0.6, y - 2.4), (-w + 0.6, y - 2.4)], fill=shade(color, 0.06 * k))
        p.pattern([(-w, y), (w, y), (w - 0.6, y - 2.4), (-w + 0.6, y - 2.4)], "checks", shade(color, -0.12), 1.2)
        p.line([(-w, y), (w, y)], shade(color, -0.4), 0.3)
    p.poly([(-6.6, -7.2), (6.6, -7.2), (5.6, -8.4), (-5.6, -8.4)], fill="#3a2418")
    for k in range(5):
        p.poly(limb((-5 + k * 2.4, -7.4), (-3.6 + k * 2.4, -9.4), 0.9, 0.8), fill="#6a3a1a")
    return (-17, -10, 17, 1)


def throne(p, color="gold", cushion="vermilion"):
    p.poly([(-11, 0), (11, 0), (10, -10), (-10, -10)], fill=shade(color, -0.05))
    p.pattern([(-11, 0), (11, 0), (10, -10), (-10, -10)], "floral", "vermilion", 2.0, 0.5)
    p.poly([(-12, -10), (12, -10), (12, -13), (-12, -13)], fill=cushion)
    p.poly([(-10, -13), (-11, -30), (-6, -36), (0, -38), (6, -36), (11, -30), (10, -13)], fill=color, smooth=True)
    p.poly([(-7, -13), (-7.6, -27), (0, -32), (7.6, -27), (7, -13)], fill=cushion, smooth=True)
    p.pattern([(-7, -13), (-7.6, -27), (0, -32), (7.6, -27), (7, -13)], "dots", "gold", 1.6, 0.4, smooth=True)
    for x in (-12, 12):
        p.circle(x, -14, 2.0, fill=color)
    return (-14, -40, 14, 1)


def chhatra_canopy(p, color="#e0a83a", accent="vermilion", w=30.0):
    dome = arc_pts(0, 0, w / 2, w * 0.2, 180, 360, 24)
    p.poly(dome + [(w / 2, 0), (-w / 2, 0)], fill=color)
    p.pattern(dome + [(w / 2, 0), (-w / 2, 0)], "vstripes", shade(color, -0.2), 2.4, 0.4)
    for k in range(int(w / 2.4)):
        x = -w / 2 + k * 2.4 + 1.2
        p.poly([(x - 1.2, 0), (x, 2.0), (x + 1.2, 0)], fill=accent)
    p.circle(0, -w * 0.2, 1.4, fill="gold")
    p.line([(0, -w * 0.2), (0, -w * 0.2 - 30)], "#efe3c4", 0.12)
    return (-w / 2 - 1, -w * 0.2 - 31, w / 2 + 1, 3)


def chariot(p, body="vermilion", trim="gold", wheel="#d8a838", flag="saffron", emblem=None):
    p.poly([(-16, -6), (16, -6), (18, -16), (-18, -16)], fill=body)
    p.pattern([(-16, -6), (16, -6), (18, -16), (-18, -16)], "dots", "gold", 1.8, 0.45)
    p.line([(-18, -16), (18, -16)], trim, 0.9)
    p.line([(-16, -6), (16, -6)], trim, 0.9)
    p.poly([(16, -10), (34, -8), (34, -7), (16, -8)], fill="#6a4428")  # yoke pole
    for x in (-10, 10):
        p.circle(x, -6, 7.4, fill=wheel)
        p.circle(x, -6, 5.6, fill=shade(wheel, -0.15))
        for k in range(8):
            a = math.radians(k * 22.5)
            p.line([(x - math.cos(a) * 5.6, -6 - math.sin(a) * 5.6), (x + math.cos(a) * 5.6, -6 + math.sin(a) * 5.6)], trim,
                   0.4)
        p.circle(x, -6, 1.4, fill="vermilion")
    p.line([(-14, -16), (-14, -40)], "#6a4428", 0.5)
    p.poly([(-14, -40), (-2, -37.4), (-3.6, -34.4), (-2, -31.6), (-14, -32)], fill=flag)
    if emblem == "hanuman":
        p.circle(-8.4, -37, 1.4, fill="#7a3a1a")
        p.poly([(-9.8, -32.6), (-8.4, -36), (-7.0, -32.6)], fill="#7a3a1a")
    return (-20, -42, 36, 2)


def boat(p, color="#8a5a32", sail=None):
    p.poly([(-16, -4), (16, -4), (12, 2), (-12, 2)], fill=color)
    p.poly([(-16, -4), (-19, -8), (-14, -4)], fill=color)
    p.poly([(16, -4), (19, -8), (14, -4)], fill=color)
    p.line([(-12, -1), (12, -1)], shade(color, -0.35), 0.3)
    if sail:
        p.line([(0, -4), (0, -24)], "#6a4428", 0.4)
        p.poly([(0.4, -23), (10, -10), (0.4, -6)], fill=sail)
    return (-20, -26, 20, 3)


def pots(p, n=3, color="#c8743a"):
    for k in range(n):
        x = (k - (n - 1) / 2) * 4.6
        y = 0 if k != n // 2 or n < 3 else 0
        p.ellipse(x, -2.6, 2.6, 2.4, fill=color)
        p.ellipse(x, -4.8, 1.3, 0.5, fill=shade(color, -0.3))
        p.line([(x - 2.4, -2.4), (x + 2.4, -2.4)], "#f2e2c0", 0.3)
    if n >= 3:
        p.ellipse(0, -7.0, 2.4, 2.2, fill=color)
        p.line([(-2.2, -6.9), (2.2, -6.9)], "#f2e2c0", 0.3)
    return (-n * 2.6 - 1, -10, n * 2.6 + 1, 0.5)


def cushion(p, color="vermilion", w=16.0):
    p.poly([(-w / 2, 0), (w / 2, 0), (w / 2 + 1, -3.2), (-w / 2 - 1, -3.2)], fill=color, smooth=True)
    p.pattern([(-w / 2, 0), (w / 2, 0), (w / 2 + 1, -3.2), (-w / 2 - 1, -3.2)], "floral", "gold", 1.6, 0.45)
    p.line([(-w / 2 - 1, -1.6), (w / 2 + 1, -1.6)], "gold", 0.4)
    return (-w / 2 - 2, -4, w / 2 + 2, 0.5)


def toran(p, w=120.0, color="#f09a2a"):
    """String of marigold garlands + mango leaves across the top."""
    for k in range(int(w / 10)):
        x0 = -w / 2 + k * 10
        pts = arc_pts(x0 + 5, 0, 5, 2.6, 0, 180, 10)
        for (gx, gy) in pts:
            p.circle(gx, gy, 0.8, fill=color if k % 2 else "#f2c94a")
        p.poly([(x0 + 5 - 1.0, 2.6), (x0 + 5, 6.6), (x0 + 5 + 1.0, 2.6)], fill="#4f7d3a", smooth=True)
    p.line([(-w / 2, 0), (w / 2, 0)], "#6a4428", 0.2)
    return (-w / 2 - 1, -1, w / 2 + 1, 8)


def bunting(p, w=120.0, colors=("vermilion", "mustard")):
    """Triangle pennant row (the stage border in the reference)."""
    p.line([(-w / 2, 0), (w / 2, 0)], "vermilion", 0.9)
    n = int(w / 6)
    for k in range(n):
        x = -w / 2 + 3 + k * 6
        p.poly([(x - 1.2, 0.5), (x + 1.2, 0.5), (x, 3.4)], fill=colors[k % len(colors)])
    return (-w / 2 - 1, -1, w / 2 + 1, 4)


def waterfall(p, h=40.0, w=8.0, color="#cfe3ea"):
    p.poly([(-w / 2, 0), (w / 2, 0), (w / 2 - 0.6, -h), (-w / 2 + 0.6, -h)], fill=mix(color, "#8ab0b8", 0.3))
    p.pattern([(-w / 2, 0), (w / 2, 0), (w / 2 - 0.6, -h), (-w / 2 + 0.6, -h)], "vstripes", color, 1.4, 0.4)
    for k in range(5):
        p.circle(-w / 2 + k * w / 4, 0, 2.0, fill="#eef4f2")
    return (-w / 2 - 3, -h - 1, w / 2 + 3, 3)


def screen(p, w=60.0, h=36.0, lit="#efe0b8", frame="#3a2418"):
    """Shadow-theatre screen with red border & pennants."""
    p.poly([(-w / 2 - 1.4, 0), (w / 2 + 1.4, 0), (w / 2 + 1.4, -h - 1.4), (-w / 2 - 1.4, -h - 1.4)], fill=frame)
    p.poly([(-w / 2, -0.6), (w / 2, -0.6), (w / 2, -h), (-w / 2, -h)], fill=lit)
    p.line([(-w / 2 - 1.6, -h - 1.0), (w / 2 + 1.6, -h - 1.0)], "vermilion", 1.2)
    for k in range(int(w / 6)):
        x = -w / 2 + 3 + k * 6
        p.poly([(x - 0.9, -h - 0.4), (x + 0.9, -h - 0.4), (x, -h + 1.8)], fill="mustard" if k % 2 else "vermilion")
    return (-w / 2 - 3, -h - 3, w / 2 + 3, 1)


def cave(p, w=60.0, h=40.0, color="#5a4a40"):
    outer = [(-w / 2, 0), (-w * 0.48, -h * 0.6), (-w * 0.3, -h * 0.95), (0, -h), (w * 0.3, -h * 0.92), (w * 0.5, -h * 0.55),
             (w / 2, 0)]
    p.poly(outer, fill=color, smooth=True)
    p.pattern(outer, "speckle", shade(color, -0.2), 2.0, 0.5, smooth=True)
    inner = [(-w * 0.3, 0), (-w * 0.28, -h * 0.5), (0, -h * 0.72), (w * 0.28, -h * 0.5), (w * 0.3, 0)]
    p.poly(inner, fill="#140e0c", smooth=True)
    return (-w / 2 - 1, -h - 1, w / 2 + 1, 1)


def steps(p, w=200.0, n=5, color="#a89878", h=14.0):
    for k in range(n):
        y0 = -k * h / n
        inset = k * 3
        p.poly([(-w / 2 + inset, y0), (w / 2 - inset, y0), (w / 2 - inset, y0 - h / n), (-w / 2 + inset, y0 - h / n)],
               fill=shade(color, 0.05 * k))
        p.line([(-w / 2 + inset, y0 - h / n), (w / 2 - inset, y0 - h / n)], shade(color, -0.35), 0.3)
    return (-w / 2 - 1, -h - 1, w / 2 + 1, 1)


def bridge_setu(p, w=120.0, color="#8a7e70"):
    r = rng("setu")
    for k in range(int(w / 5)):
        x = -w / 2 + k * 5 + r.uniform(-0.6, 0.6)
        rr = r.uniform(2.2, 3.4)
        p.ellipse(x, -rr * 0.6, rr, rr * 0.7, fill=shade(color, r.uniform(-0.1, 0.1)))
        if r.random() < 0.5:
            p.line([(x - 1, -rr * 0.6), (x + 1, -rr * 0.7)], "#b84a2a", 0.3)
    return (-w / 2 - 4, -5, w / 2 + 4, 1)


def mount_meru(p, color="#8a6a4a", h=50.0):
    pts = [(-30, 0), (-18, -h * 0.5), (-8, -h * 0.9), (0, -h), (9, -h * 0.85), (20, -h * 0.45), (30, 0)]
    p.poly(pts, fill=color, smooth=True)
    p.pattern(pts, "speckle", "#9fd08a", 2.2, 0.6, smooth=True)
    for k in range(6):
        p.circle(-12 + k * 5, -h * 0.4 - (k % 2) * 6, 1.2, fill="#e0f0a0")
    return (-31, -h - 1, 31, 1)


PROPS = {
    "cloud": cloud, "sun": sun, "moon": moon, "star": star, "tree": tree, "bush": bush, "lotus": lotus, "grass": grass,
    "rock": rock, "mountains": mountains, "palace": palace, "pillar": pillar, "temple": temple, "fort": fort,
    "city": city, "hut": hut, "tent": tent, "flagpole": flagpole, "deepstambh": deepstambh, "diya": diya_prop,
    "yagya_kund": yagya_kund, "throne": throne, "chhatra": chhatra_canopy, "chariot": chariot, "boat": boat,
    "pots": pots, "cushion": cushion, "toran": toran, "bunting": bunting, "waterfall": waterfall, "screen": screen,
    "cave": cave, "steps": steps, "setu": bridge_setu, "sanjeevani_mountain": mount_meru,
}

class NullPen:
    """Accepts every Pen call and draws nothing (used to query prop bounds)."""

    def __getattr__(self, name):
        return lambda *a, **k: None


def prop_bounds(name, **params):
    return PROPS[name](NullPen(), **params)


# props that hang from the fly-loft on strings (sway animated)
HANGING = {"cloud", "sun", "moon", "star", "chhatra"}


def build_prop(name, ppu, use_cache=True, **params):
    key = stable_hash({"n": name, "p": params, "ppu": round(ppu, 3), "v": PROP_VERSION})
    cp = CACHE_DIR / "props" / f"{name}_{key}.pkl"
    if use_cache and cp.exists():
        try:
            with open(cp, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    fn = PROPS[name]
    # first pass: measure bounds without drawing
    bounds = fn(NullPen(), **params)
    big = (bounds[2] - bounds[0]) * ppu > 2400
    pen = Pen(bounds, ppu, ss=2 if big else 3)
    fn(pen, **params)
    ow = 0.3 if name not in ("mountains", "city") else 0.18
    spr = pen.finish(ow=ow, inner=0.22, texture=0.9)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with open(cp, "wb") as f:
            pickle.dump(spr, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return spr
