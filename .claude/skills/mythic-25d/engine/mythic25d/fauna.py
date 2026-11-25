"""Jointed paper-puppet animals, birds and serpents (facing right).

Quadruped parts: body, head (neck+head), 4 legs (near/far, fore/hind), tail.
Bird parts: body (incl. head + legs), wing_f, wing_b, tail.
Serpent: coiled body + hood (single sway part).
Species are parameter dicts in data/animals.json & data/birds.json; anything
missing falls back to the archetype defaults below.
"""
from __future__ import annotations

import math
import pickle

from .gfx import Pen, arc_pts, catmull, limb, rot
from .rig import Part, Rig
from .util import code_version, CACHE_DIR, shade, stable_hash

FAUNA_VERSION = code_version("fauna", "gfx")
INK = "ink"

ARCHETYPES = {
    "horse":    dict(L=34, H=14, leg=24, lw=4.6, neck=13, neck_ang=-52, head="horse", ears="pointed", tail="long", foot="hoof", mane=True, color="#efe6d2"),
    "cow":      dict(L=36, H=16, leg=19, lw=5.0, neck=8, neck_ang=-20, head="bovine", ears="side", horns="curved", tail="tuft", foot="hoof", hump=0, color="#f0e8d8"),
    "bull":     dict(L=38, H=17, leg=19, lw=5.6, neck=8, neck_ang=-15, head="bovine", ears="side", horns="curved", tail="tuft", foot="hoof", hump=4, color="#f2ecdc", dewlap=True),
    "buffalo":  dict(L=38, H=17, leg=17, lw=6.0, neck=6, neck_ang=-5, head="bovine", ears="side", horns="buffalo", tail="tuft", foot="hoof", color="#3a3430"),
    "elephant": dict(L=42, H=26, leg=19, lw=9.0, neck=3, neck_ang=0, head="elephant", tail="thin", foot="pad", color="#8d8a86"),
    "lion":     dict(L=32, H=13, leg=16, lw=5.0, neck=6, neck_ang=-35, head="feline", head_scale=1.45, ears="round", tail="tuft", foot="paw", mane=True, color="#d9a04a"),
    "tiger":    dict(L=34, H=12, leg=15, lw=5.0, neck=5, neck_ang=-25, head="feline", head_scale=1.3, ears="round", tail="long_cat", foot="paw", pattern="tiger", color="#e08a2c"),
    "leopard":  dict(L=30, H=10, leg=14, lw=4.2, neck=5, neck_ang=-25, head="feline", ears="round", tail="long_cat", foot="paw", pattern="leopard", color="#e0b050"),
    "deer":     dict(L=26, H=11, leg=21, lw=2.8, neck=11, neck_ang=-62, head="deer", ears="long", horns="antler", tail="short", foot="hoof", pattern="spots", color="#c98a44"),
    "dog":      dict(L=22, H=9, leg=13, lw=3.0, neck=6, neck_ang=-45, head="canine", ears="pointed", tail="curl", foot="paw", color="#a87a4a"),
    "wolf":     dict(L=26, H=10, leg=15, lw=3.4, neck=6, neck_ang=-35, head="canine", ears="pointed", tail="bushy", foot="paw", color="#7c7468"),
    "boar":     dict(L=28, H=13, leg=10, lw=4.0, neck=3, neck_ang=-5, head="boar", ears="pointed", tail="short", foot="hoof", color="#5a4434"),
    "bear":     dict(L=30, H=15, leg=12, lw=6.0, neck=5, neck_ang=-10, head="bear", ears="round", tail="short", foot="paw", color="#3e3028"),
    "goat":     dict(L=24, H=10, leg=15, lw=2.8, neck=8, neck_ang=-55, head="goat", ears="droopy", horns="back", tail="short", foot="hoof", beard=True, color="#e8e0d0"),
    "ram":      dict(L=26, H=12, leg=14, lw=3.2, neck=7, neck_ang=-45, head="goat", ears="droopy", horns="spiral", tail="short", foot="hoof", pattern="wool", color="#efe8da"),
    "camel":    dict(L=32, H=13, leg=28, lw=3.8, neck=18, neck_ang=-28, head="camel", head_scale=1.4, ears="small", tail="tuft", foot="pad", hump=7, color="#c8a066"),
    "donkey":   dict(L=28, H=12, leg=18, lw=3.8, neck=9, neck_ang=-48, head="horse", ears="long", tail="tuft", foot="hoof", mane=True, color="#8a8076"),
    "rabbit":   dict(L=11, H=8, leg=4, lw=2.4, neck=2, neck_ang=-40, head="rabbit", ears="rabbit", tail="puff", foot="paw", color="#efe6d8"),
    "rat":      dict(L=9, H=5, leg=2.5, lw=1.6, neck=1.5, neck_ang=-10, head="rodent", ears="round", tail="thin", foot="paw", color="#7a6e64"),
    "cat":      dict(L=16, H=7, leg=8, lw=2.2, neck=4, neck_ang=-45, head="feline", ears="pointed", tail="long_cat", foot="paw", color="#c08a52"),
    "monkey":   dict(L=16, H=8, leg=10, lw=2.4, neck=3, neck_ang=-30, head="monkey", ears="round", tail="curl_long", foot="paw", color="#a8784a"),
    "rhino":    dict(L=38, H=18, leg=13, lw=7.0, neck=4, neck_ang=-5, head="rhino", ears="small", tail="thin", foot="pad", color="#8a8278"),
    "jackal":   dict(L=22, H=8, leg=13, lw=2.8, neck=6, neck_ang=-35, head="canine", ears="pointed", tail="bushy", foot="paw", color="#b08a58"),
}


# real-world size relative to a standing human puppet (applied on stage)
SIZE_K = {"horse": 1.9, "cow": 1.7, "bull": 1.8, "buffalo": 1.75, "elephant": 2.5, "lion": 1.75, "tiger": 1.75,
          "leopard": 1.45, "deer": 1.55, "dog": 1.05, "wolf": 1.15, "boar": 1.2, "bear": 1.6, "goat": 1.05, "ram": 1.1,
          "camel": 2.0, "donkey": 1.5, "rabbit": 0.75, "rat": 0.7, "cat": 0.85, "monkey": 1.0, "rhino": 1.9, "jackal": 1.05}
BIRD_K = 2.3


def size_factor(spec):
    kind = spec.get("kind", "quadruped")
    if kind == "bird":
        return BIRD_K
    if kind in ("serpent", "fish"):
        return 1.6
    return SIZE_K.get(spec.get("base", spec.get("id")), 1.4)


def _r(sp, k, d=None):
    return sp.get(k, d)


# =========================================================================== quadruped parts

def _q_body(sp, ppu):
    L, H = sp["L"], sp["H"]
    p = Pen((-L * 0.75, -H * 1.3 - sp.get("hump", 0) - 2, L * 0.75, H * 0.8), ppu)
    c = sp["color"]
    hump = sp.get("hump", 0)
    pts = [(L * 0.48, -H * 0.62), (L * 0.18, -H * 0.72 - hump * 0.4), (L * 0.05, -H * 0.8 - hump),
           (-L * 0.1, -H * 0.72 - hump * 0.2), (-L * 0.4, -H * 0.66), (-L * 0.54, -H * 0.4), (-L * 0.52, H * 0.05),
           (-L * 0.32, H * 0.42), (0, H * 0.5), (L * 0.3, H * 0.44), (L * 0.52, H * 0.1), (L * 0.56, -H * 0.3)]
    if sp.get("head") == "elephant":
        pts = [(L * 0.45, -H * 0.55), (L * 0.1, -H * 0.85), (-L * 0.25, -H * 0.8), (-L * 0.5, -H * 0.45),
               (-L * 0.52, H * 0.1), (-L * 0.3, H * 0.45), (L * 0.2, H * 0.48), (L * 0.5, H * 0.15)]
    p.poly(pts, fill=c, smooth=True)
    pat = sp.get("pattern")
    if pat == "tiger":
        p.pattern(pts, "tiger", INK, 3.2, 0.9, smooth=True)
    elif pat == "leopard":
        p.pattern(pts, "leopard", "#3a2414", 3.0, 0.9, smooth=True)
    elif pat == "spots":
        p.pattern(pts, "dots", "#f6efdf", 3.0, 0.9, smooth=True)
    elif pat == "wool":
        p.pattern(pts, "scales", shade(c, -0.2), 2.0, 0.5, smooth=True)
    else:
        p.pattern(pts, "speckle", shade(c, -0.12), 2.6, 0.35, smooth=True)
    # belly line + shoulder/hip muscle arcs (folk line work)
    lc = shade(c, -0.4)
    p.line(arc_pts(L * 0.32, -H * 0.05, H * 0.36, H * 0.42, 120, 240, 10), lc, 0.22)
    p.line(arc_pts(-L * 0.32, -H * 0.05, H * 0.36, H * 0.42, -60, 60, 10), lc, 0.22)
    if sp.get("dewlap"):
        p.poly([(L * 0.5, -H * 0.2), (L * 0.6, H * 0.1), (L * 0.42, H * 0.36)], fill=c, smooth=True)
    # caparison: saddle cloth (horses) / jhool (elephants) / garland
    cloth = sp.get("cloth")
    if cloth:
        cc = cloth if isinstance(cloth, str) else "vermilion"
        if sp.get("head") == "elephant":
            cl = [(-L * 0.28, -H * 0.82), (L * 0.22, -H * 0.84), (L * 0.28, H * 0.2), (-L * 0.34, H * 0.2)]
        else:
            cl = [(-L * 0.22, -H * 0.72), (L * 0.18, -H * 0.74), (L * 0.2, H * 0.12), (-L * 0.24, H * 0.12)]
        p.poly(cl, fill=cc, smooth=True, n=4)
        p.pattern(cl, "floral", "gold", 2.0, 0.6, smooth=True, color2="cream")
        p.line(catmull(cl, True, 4) + [catmull(cl, True, 4)[0]], "gold", 0.6)
        for k in range(7):
            x = cl[3][0] + (cl[2][0] - cl[3][0]) * k / 6
            p.circle(x, cl[2][1] + 0.9, 0.5, fill="gold")
    if sp.get("bells"):
        p.line(arc_pts(L * 0.5, -H * 0.4, 3.0, 4.0, 60, 160, 10), "gold", 0.4)
    p.rivet(L * 0.36, -H * 0.2, 0.9)
    p.rivet(-L * 0.36, -H * 0.2, 0.9)
    return p.finish(seed=21)


def _q_leg(sp, ppu, near=True, fore=True):
    leg, lw = sp["leg"], sp["lw"]
    c = sp["color"] if near else shade(sp["color"], -0.16)
    p = Pen((-lw * 1.6, -lw, lw * 1.8, leg + lw * 1.2), ppu)
    foot = sp.get("foot", "hoof")
    if foot == "pad":  # elephant / camel pillars
        p.poly(limb((0, 0), (0, leg), lw, lw * 0.92), fill=c)
        p.ellipse(0.2, leg + 0.2, lw * 0.56, lw * 0.22, fill=shade(c, 0.1))
        for k in range(3):
            p.circle(-lw * 0.28 + k * lw * 0.28 + 0.3, leg + 0.1, lw * 0.1, fill="#efe6d0")
        if sp.get("anklet", True) and sp.get("head") == "elephant":
            p.poly(limb((-lw * 0.5, leg * 0.8), (lw * 0.5, leg * 0.8), 1.0, 1.0), fill="gold")
    else:
        knee = leg * (0.45 if fore else 0.42)
        bend = 1 if fore else -1
        pts = catmull([(0, 0), (bend * -0.4, knee * 0.6), (bend * 0.5, knee), (bend * -0.2, leg * 0.8), (0.2, leg)],
                      False, 6)
        for i in range(len(pts) - 1):
            w = lw * (1.0 - 0.45 * i / len(pts))
            p.poly(limb(pts[i], pts[i + 1], w, w * 0.97), fill=c)
        if foot == "hoof":
            p.poly([(-lw * 0.36, leg - 0.6), (lw * 0.5, leg - 0.6), (lw * 0.6, leg + 1.4), (-lw * 0.4, leg + 1.4)],
                   fill="#3a2a20")
        else:
            p.ellipse(lw * 0.4, leg + 0.4, lw * 0.62, lw * 0.34, fill=c)
            for k in range(3):
                p.line([(lw * 0.2 + k * 0.4, leg + 0.1), (lw * 0.3 + k * 0.4, leg + 0.7)], INK, 0.12)
        if not sp.get("no_bands") and near:
            p.poly(limb((-lw * 0.4, leg * 0.78), (lw * 0.4, leg * 0.78), 0.5, 0.5), fill="gold" if sp.get("cloth") else shade(c, -0.25))
    p.rivet(0, 0, min(0.9, lw * 0.22))
    return p.finish(seed=22 + near + fore * 2)


def _ears(p, kind, x, y, c):
    if kind == "pointed":
        p.poly([(x - 0.8, y), (x - 1.6, y - 3.8), (x + 0.6, y - 0.6)], fill=c, outline=INK, w=0.12)
    elif kind == "long":
        p.poly([(x - 0.4, y), (x - 3.6, y - 4.4), (x - 4.0, y - 3.2), (x + 0.4, y + 0.4)], fill=c, smooth=True)
    elif kind == "rabbit":
        p.poly([(x, y), (x - 1.6, y - 6.4), (x - 0.4, y - 6.6), (x + 0.8, y)], fill=c, smooth=True)
        p.poly([(x - 0.3, y - 0.5), (x - 1.2, y - 5.4), (x - 0.5, y - 5.6), (x + 0.4, y - 0.5)], fill="#e8a6a0", smooth=True)
    elif kind == "round":
        p.circle(x - 0.6, y - 0.8, 1.3, fill=c, outline=INK, w=0.12)
        p.circle(x - 0.6, y - 0.8, 0.6, fill=shade(c, -0.25))
    elif kind == "droopy":
        p.poly([(x, y), (x - 3.2, y + 2.4), (x - 2.6, y + 3.2), (x + 0.6, y + 0.8)], fill=shade(c, -0.08), smooth=True)
    elif kind == "side":
        p.poly([(x, y), (x - 3.6, y - 0.6), (x - 3.0, y + 1.0), (x + 0.4, y + 0.8)], fill=shade(c, -0.08), smooth=True)
    elif kind == "small":
        p.circle(x - 0.4, y - 0.4, 0.8, fill=c, outline=INK, w=0.1)


def _horns(p, kind, x, y, c="#e8dcc0"):
    if kind == "curved":
        p.poly([(x - 0.4, y), (x - 1.6, y - 3.4), (x - 0.4, y - 5.2), (x + 0.4, y - 4.6), (x - 0.4, y - 3.0), (x + 0.8, y)],
               fill=c, smooth=True, outline=INK, w=0.12)
    elif kind == "buffalo":
        p.poly([(x + 1.0, y), (x - 4.0, y - 1.2), (x - 7.0, y - 3.8), (x - 6.4, y - 5.2), (x - 3.4, y - 3.2), (x + 1.6, y - 1.6)],
               fill=c, smooth=True, outline=INK, w=0.12)
    elif kind == "antler":
        col = "#8a6a44"
        p.line([(x, y), (x - 1.0, y - 4.0), (x - 0.4, y - 7.6)], col, 0.5, smooth=True)
        p.line([(x - 0.8, y - 3.2), (x + 1.6, y - 5.2)], col, 0.4)
        p.line([(x - 0.7, y - 5.6), (x - 2.8, y - 7.2)], col, 0.4)
        p.line([(x - 0.5, y - 6.8), (x + 1.2, y - 8.6)], col, 0.36)
    elif kind == "back":
        p.poly([(x, y), (x - 2.6, y - 2.6), (x - 3.8, y - 2.0), (x - 0.4, y + 0.6)], fill="#9a8a70", smooth=True)
    elif kind == "spiral":
        p.line(arc_pts(x - 1.4, y - 0.4, 2.2, 2.2, -90, 250, 20), "#c8b48a", 0.9)


def _q_head(sp, ppu):
    """Neck + head; pivot at the neck base on the body (front-top)."""
    c = sp["color"]
    neck, ang = sp["neck"], sp["neck_ang"]
    kind = sp["head"]
    S = sp.get("head_scale", 1.0) * (sp["H"] / 14.0) ** 0.5 if kind != "elephant" else sp["H"] / 26.0 * 1.6
    p = Pen((-14 * S - 4, -neck - 18 * S, neck * 0.9 + 20 * S, 14 * S + 6), ppu)
    a = math.radians(ang)
    hx, hy = math.cos(a) * neck, math.sin(a) * neck
    # neck
    nw = sp["H"] * 0.62
    if kind not in ("elephant",):
        p.poly(limb((0, 0), (hx, hy), nw, nw * 0.6), fill=c)
        if sp.get("mane") and kind == "horse":
            mpts = [(-nw * 0.3, -nw * 0.4), (hx - 1.2, hy - 1.6), (hx - 2.4, hy - 0.4), (-nw * 0.6, nw * 0.1)]
            p.poly(mpts, fill=sp.get("mane_color", "#3a2818"), smooth=True)
            p.pattern(mpts, "stripes", "#5a4028", 0.8, 0.2, smooth=True)
    hc = c

    def H(pts):  # head-local -> pen
        return [(hx + x * S, hy + y * S) for x, y in pts]

    if kind == "horse":
        head = H([(-2.4, -1.6), (0.6, -2.8), (4.6, -0.6), (8.6, 2.4), (9.2, 4.2), (7.6, 5.0), (3.4, 3.8), (-1.6, 2.6)])
        p.poly(head, fill=hc, smooth=True)
        _ears(p, sp.get("ears", "pointed"), *H([(-0.8, -2.0)])[0], hc)
        p.circle(*H([(8.2, 3.2)])[0], 0.35 * S, fill=INK)
        ex, ey = H([(1.6, -0.6)])[0]
        p.ellipse(ex, ey, 0.9 * S, 0.55 * S, fill="#f6ecd6", outline=INK, w=0.15)
        p.circle(ex + 0.25 * S, ey, 0.32 * S, fill=INK)
        if sp.get("cloth"):
            p.line(H([(-1.0, -1.4), (3.0, 2.8), (8.0, 4.2)]), "vermilion", 0.45 * S)
            p.circle(*H([(1.2, -2.6)])[0], 0.9 * S, fill="vermilion")
            p.poly(H([(0.6, -2.8), (0.0, -6.0), (1.8, -3.0)]), fill="#f6efdf", smooth=True)
    elif kind == "bovine":
        head = H([(-2.0, -2.0), (1.6, -2.4), (5.4, 0.6), (6.8, 3.8), (5.6, 5.4), (2.4, 4.6), (-1.6, 2.4)])
        p.poly(head, fill=hc, smooth=True)
        p.ellipse(*H([(5.8, 4.4)])[0], 1.3 * S, 1.0 * S, fill=shade(hc, -0.18) if sp["color"] != "#3a3430" else "#5a4a40")
        p.circle(*H([(6.0, 4.0)])[0], 0.28 * S, fill=INK)
        _horns(p, sp.get("horns", "curved"), *H([(0.2, -2.0)])[0], sp.get("horn_color", "#e8dcc0"))
        _ears(p, "side", *H([(-0.8, -0.8)])[0], hc)
        ex, ey = H([(1.8, 0.2)])[0]
        p.ellipse(ex, ey, 0.95 * S, 0.6 * S, fill="#f6ecd6", outline=INK, w=0.15)
        p.circle(ex + 0.25 * S, ey, 0.34 * S, fill=INK)
        if sp.get("tilak", True):
            p.line(H([(2.4, -1.6), (3.0, 0.2)]), "vermilion", 0.4 * S)
        if sp.get("bells") or sp.get("cloth"):
            p.line(H([(-2.4, 2.4), (-0.6, 4.6), (1.2, 4.8)]), "gold", 0.4 * S, smooth=True)
            p.circle(*H([(-0.6, 5.4)])[0], 0.8 * S, fill="gold")
    elif kind == "elephant":
        head = H([(-4.0, -6.0), (1.0, -8.4), (6.0, -6.4), (8.0, -2.0), (7.0, 2.0), (3.0, 3.6), (-3.0, 3.0)])
        p.poly(head, fill=hc, smooth=True)
        ear = H([(-1.0, -6.4), (-7.6, -6.0), (-9.0, 0.6), (-6.6, 6.0), (-2.0, 4.4)])
        p.poly(ear, fill=shade(hc, -0.06), smooth=True)
        p.pattern(ear, "speckle", "#d8a0a0", 1.2, 0.4, smooth=True)
        path = catmull(H([(6.8, -1.0), (8.6, 3.6), (8.8, 9.0), (8.0, 13.6), (9.6, 15.6), (10.8, 14.6)]), False, 6)
        for i in range(len(path) - 1):
            w = (3.2 - 1.9 * i / len(path)) * S
            p.poly(limb(path[i], path[i + 1], w, w), fill=hc)
        for i in range(2, len(path) - 2, 2):
            x, y = path[i]
            p.line([(x - 1.1 * S, y), (x + 1.1 * S, y)], shade(hc, -0.3), 0.14 * S)
        p.poly(H([(6.2, 1.6), (10.6, 2.6), (12.0, 1.2), (6.6, 0.0)]), fill="#f6efdf", smooth=True, outline=INK, w=0.12)
        ex, ey = H([(4.2, -3.0)])[0]
        p.ellipse(ex, ey, 0.9 * S, 0.5 * S, fill="#f6ecd6", outline=INK, w=0.12)
        p.circle(ex + 0.2 * S, ey, 0.3 * S, fill=INK)
        if sp.get("cloth"):
            hp = H([(0.0, -8.0), (5.6, -6.6), (7.4, -1.6), (5.2, -2.8), (2.0, -5.2)])
            p.poly(hp, fill="vermilion", smooth=True)
            p.pattern(hp, "dots", "gold", 1.0, 0.4, smooth=True)
            p.line(catmull(hp, False, 4), "gold", 0.4)
        if sp.get("white"):
            pass
    elif kind == "feline":
        if sp.get("mane"):
            spikes = []
            for k in range(15):
                aa = math.radians(-230 + k * 17)
                r = 6.2 * S if k % 2 == 0 else 4.6 * S
                spikes.append((hx + 0.6 * S + math.cos(aa) * r, hy + 0.8 * S + math.sin(aa) * r))
            p.poly(spikes, fill=sp.get("mane_color", "#9a5a26"))
        head = H([(-2.2, -2.2), (1.4, -3.0), (4.2, -1.6), (5.6, 0.6), (5.2, 2.6), (2.4, 3.6), (-1.6, 2.4)])
        p.poly(head, fill=hc, smooth=True)
        if sp.get("pattern") == "tiger":
            p.pattern(head, "tiger", INK, 1.6, 0.4, smooth=True)
        p.poly(H([(3.0, 1.0), (5.6, 0.8), (5.4, 2.6), (2.8, 3.0)]), fill="#f2e2c0", smooth=True)
        p.circle(*H([(5.4, 0.8)])[0], 0.45 * S, fill=INK)
        _ears(p, "round" if sp.get("ears") != "pointed" else "pointed", *H([(-0.6, -2.4)])[0], hc)
        ex, ey = H([(2.0, -0.8)])[0]
        p.ellipse(ex, ey, 0.9 * S, 0.6 * S, fill="#f2d36a", outline=INK, w=0.15)
        p.circle(ex + 0.2 * S, ey, 0.28 * S, fill=INK)
        for k in range(3):
            p.line(H([(4.2, 1.6 + k * 0.4), (7.0, 1.2 + k * 0.8)]), INK, 0.1)
    elif kind in ("deer", "goat", "camel", "canine", "rabbit", "rodent", "monkey", "rhino", "boar", "bear"):
        snout = {"deer": 4.6, "goat": 4.2, "camel": 5.0, "canine": 5.4, "rabbit": 2.4, "rodent": 3.4, "monkey": 2.6,
                 "rhino": 6.0, "boar": 6.4, "bear": 4.6}[kind]
        hh = {"rabbit": 2.6, "rodent": 2.0, "monkey": 3.0, "rhino": 4.0, "boar": 3.6, "bear": 3.6}.get(kind, 2.6)
        head = H([(-2.0, -hh), (1.4, -hh - 0.4), (snout * 0.7, -hh * 0.2), (snout + 1.6, hh * 0.3),
                  (snout + 1.2, hh * 0.9), (snout * 0.5, hh * 1.0), (-1.6, hh * 0.9)])
        p.poly(head, fill=hc, smooth=True)
        p.circle(*H([(snout + 1.0, hh * 0.35)])[0], 0.35 * S, fill=INK)
        _ears(p, sp.get("ears", "pointed"), *H([(-0.6, -hh * 0.9)])[0], hc)
        if sp.get("horns"):
            _horns(p, sp["horns"], *H([(0.0, -hh)])[0])
        if kind == "rhino":
            p.poly(H([(snout - 0.4, -hh * 0.2), (snout + 0.6, -hh * 1.6), (snout + 1.4, -hh * 0.1)]), fill="#d8ccb4",
                   outline=INK, w=0.12)
        if kind == "boar":
            p.poly(H([(snout - 0.6, hh * 0.6), (snout + 0.2, -hh * 0.4), (snout + 0.6, hh * 0.4)]), fill="#f6efdf",
                   outline=INK, w=0.12)
        if sp.get("beard"):
            p.poly(H([(snout * 0.4, hh * 0.9), (snout * 0.2, hh * 2.4), (snout * 0.6, hh * 1.0)]), fill=shade(hc, -0.1))
        if kind == "monkey":
            p.ellipse(*H([(snout * 0.6, hh * 0.3)])[0], 1.8 * S, 1.6 * S, fill="#f0dcb0")
        ex, ey = H([(1.6, -hh * 0.35)])[0]
        p.ellipse(ex, ey, 0.8 * S, 0.5 * S, fill="#f6ecd6", outline=INK, w=0.14)
        p.circle(ex + 0.2 * S, ey, 0.28 * S, fill=INK)
    p.rivet(0, 0, 0.8)
    return p.finish(seed=23)


def _q_tail(sp, ppu):
    c = sp["color"]
    kind = sp.get("tail", "thin")
    p = Pen((-16, -16, 6, 20), ppu)
    if kind == "long":
        pts = [(0, 0), (-3.0, 3.0), (-4.6, 8.0), (-4.0, 13.0), (-5.6, 17.0)]
        col = sp.get("mane_color", "#3a2818")
        p.poly([(0.6, -0.6), (-2.6, 2.0), (-5.6, 8.0), (-6.4, 16.0), (-4.4, 18.0), (-3.2, 12.0), (-2.0, 6.0), (0.8, 1.6)],
               fill=col, smooth=True)
        p.pattern([(0, 0), (-5.6, 8.0), (-6.4, 16.0), (-3.2, 12.0)], "stripes", shade(col, 0.2), 0.9, 0.2)
    elif kind in ("long_cat", "curl_long"):
        pts = catmull([(0, 0), (-4.0, -1.0), (-8.0, -4.0), (-10.0, -9.0), (-8.6, -12.0)], False, 6)
        for i in range(len(pts) - 1):
            p.poly(limb(pts[i], pts[i + 1], 1.6, 1.5), fill=c)
        if sp.get("pattern") == "tiger":
            for i in range(1, len(pts) - 1, 3):
                x, y = pts[i]
                p.line([(x - 0.8, y - 0.6), (x + 0.8, y + 0.6)], INK, 0.4)
    elif kind == "bushy":
        p.poly([(0.4, -0.4), (-4.0, 1.6), (-8.4, 5.0), (-9.6, 8.6), (-6.8, 8.0), (-3.0, 4.6), (0.4, 1.4)], fill=c, smooth=True)
    elif kind == "curl":
        pts = catmull([(0, 0), (-2.0, -2.6), (-1.6, -5.4), (0.6, -5.6), (0.8, -3.8)], False, 6)
        for i in range(len(pts) - 1):
            p.poly(limb(pts[i], pts[i + 1], 1.4, 1.2), fill=c)
    elif kind == "puff":
        p.circle(-0.8, 0, 1.6, fill="#f8f2e6")
    elif kind == "short":
        p.poly(limb((0, 0), (-1.6, 2.6), 1.4, 0.8), fill=c)
    else:  # thin / tuft
        pts = catmull([(0, 0), (-1.6, 3.0), (-2.2, 7.0), (-2.0, 11.0)], False, 6)
        for i in range(len(pts) - 1):
            p.poly(limb(pts[i], pts[i + 1], 0.9, 0.8), fill=c)
        if kind == "tuft":
            p.poly([(-2.6, 10.0), (-1.4, 10.0), (-0.8, 13.6), (-2.0, 14.6), (-3.4, 13.4)], fill="#3a2818", smooth=True)
    p.rivet(0, 0, 0.6)
    return p.finish(seed=24)


def resolve_animal(spec):
    base = dict(ARCHETYPES.get(spec.get("base", spec.get("id", "horse")), ARCHETYPES["horse"]))
    base.update({k: v for k, v in spec.items() if v is not None})
    return base


def build_quadruped(spec, ppu=9.0):
    sp = resolve_animal(spec)
    L, H = sp["L"], sp["H"]
    rig = Rig(spec.get("id", "animal"), ppu)
    rig.meta = {"spec": sp, "kind": "quadruped"}
    rig.add(Part("body", _q_body(sp, ppu), None, (0, 0), z=10))
    shoulder_x, hip_x = L * 0.36, -L * 0.36
    leg_y = -H * 0.2
    rig.add(Part("leg_ff", _q_leg(sp, ppu, near=False, fore=True), "body", (shoulder_x - 1.5, leg_y), z=2))
    rig.add(Part("leg_hf", _q_leg(sp, ppu, near=False, fore=False), "body", (hip_x + 1.5, leg_y), z=2))
    rig.add(Part("leg_fn", _q_leg(sp, ppu, near=True, fore=True), "body", (shoulder_x, leg_y), z=12))
    rig.add(Part("leg_hn", _q_leg(sp, ppu, near=True, fore=False), "body", (hip_x, leg_y), z=12))
    nx = L * 0.46 if sp["head"] != "elephant" else L * 0.42
    ny = -H * 0.45 if sp["head"] != "elephant" else -H * 0.4
    rig.add(Part("head", _q_head(sp, ppu), "body", (nx, ny), z=14 if sp["head"] != "elephant" else 15))
    rig.add(Part("tail", _q_tail(sp, ppu), "body", (-L * 0.52, -H * 0.42), z=1))
    rig.ground = sp["leg"] + 1.2 - H * 0.2
    span = max(L, sp["leg"] + H) * 1.25 + 12
    rig.extent = (-span, -span * 1.1, span, sp["leg"] + 6)
    rig.anchors = {"head": ("head", (0, -4)), "back": ("body", (0, -H * 0.7))}
    rig.meta["scale"] = sp.get("scale", 1.0) * size_factor(dict(spec, kind="quadruped"))
    return rig


# =========================================================================== birds

BIRDS = {
    "peacock":  dict(size=1.0, body="#1f5aa8", wing="#2f7a54", head="#1f5aa8", beak="short", neck=4.0, leg=6, tail="peacock", crest="peacock"),
    "hamsa":    dict(size=1.1, body="#f6efdf", wing="#ece2cc", head="#f6efdf", beak="flat", beak_color="#e8833a", neck=7.0, leg=3, tail="short", crest=None, swim=True),
    "swan":     dict(size=1.1, body="#f6efdf", wing="#ece2cc", head="#f6efdf", beak="flat", beak_color="#e8833a", neck=7.0, leg=3, tail="short", swim=True),
    "eagle":    dict(size=1.0, body="#6a4428", wing="#5a3820", head="#efe6d0", beak="hook", neck=1.5, leg=4, tail="short"),
    "vulture":  dict(size=1.2, body="#4a3a30", wing="#3a2c24", head="#c98a6a", beak="hook", neck=3.0, leg=4.5, tail="short", ruff=True),
    "owl":      dict(size=0.8, body="#9a7a54", wing="#7a5a3a", head="#9a7a54", beak="hook", neck=0.2, leg=2, tail="short", owl=True),
    "crow":     dict(size=0.7, body="#23201f", wing="#1a1817", head="#3a3634", beak="cone", neck=1.0, leg=3, tail="short"),
    "parrot":   dict(size=0.7, body="#3f9a4a", wing="#2f7a3a", head="#3f9a4a", beak="hook", beak_color="#c8321f", neck=1.0, leg=2.5, tail="long", ring=True),
    "crane":    dict(size=1.1, body="#e6e2da", wing="#9a9a9a", head="#c8321f", beak="long", neck=9.0, leg=13, tail="short"),
    "heron":    dict(size=1.0, body="#d8d8d0", wing="#9aa0a8", head="#e6e6e0", beak="long", neck=8.0, leg=11, tail="short"),
    "sparrow":  dict(size=0.45, body="#a8784a", wing="#7a5434", head="#7a5434", beak="cone", neck=0.5, leg=2, tail="short"),
    "pigeon":   dict(size=0.6, body="#8a8e9a", wing="#7a7e8a", head="#6a6e7a", beak="cone", neck=1.2, leg=2, tail="short"),
    "rooster":  dict(size=0.8, body="#c8521f", wing="#8a3a1a", head="#c8521f", beak="cone", neck=2.0, leg=5, tail="rooster", crest="comb"),
    "hen":      dict(size=0.7, body="#c8964a", wing="#a8763a", head="#c8964a", beak="cone", neck=1.6, leg=4, tail="short", crest="comb"),
    "kingfisher": dict(size=0.5, body="#e8833a", wing="#2a7ab8", head="#2a7ab8", beak="long", beak_color="#c8321f", neck=0.6, leg=1.6, tail="short"),
    "koel":     dict(size=0.55, body="#1e1c22", wing="#16141a", head="#1e1c22", beak="cone", beak_color="#c8c070", neck=0.8, leg=2, tail="long"),
    "myna":     dict(size=0.5, body="#5a3a2a", wing="#2a2220", head="#1e1a18", beak="cone", beak_color="#f2c23a", neck=0.8, leg=2.2, tail="short"),
    "hornbill": dict(size=0.9, body="#2a2626", wing="#1e1a1a", head="#2a2626", beak="horn", beak_color="#f2c23a", neck=1.4, leg=3, tail="long"),
    "flamingo": dict(size=1.1, body="#f0a0a8", wing="#e8808a", head="#f0a0a8", beak="bent", neck=9.0, leg=14, tail="short"),
    "kite":     dict(size=0.9, body="#7a5434", wing="#5a3c24", head="#9a7454", beak="hook", neck=1.0, leg=3, tail="forked"),
    "falcon":   dict(size=0.8, body="#6a6a72", wing="#4a4a52", head="#3a3a42", beak="hook", neck=1.0, leg=3, tail="short"),
    "stork":    dict(size=1.1, body="#f0ece4", wing="#2a2626", head="#f0ece4", beak="long", beak_color="#c8521f", neck=6.0, leg=12, tail="short"),
    "duck":     dict(size=0.7, body="#a88a5a", wing="#7a6a4a", head="#2f6a4a", beak="flat", beak_color="#e8b03a", neck=2.4, leg=2, tail="short", swim=True),
    "chakravak": dict(size=0.8, body="#d8843a", wing="#a85a2a", head="#efe0c0", beak="flat", beak_color="#2a2626", neck=2.6, leg=3, tail="short", swim=True),
    "garuda_bird": dict(size=1.4, body="#c8642a", wing="#e0a040", head="#efe6d0", beak="hook", beak_color="#f2c23a", neck=2.0, leg=5, tail="long"),
    "bulbul":   dict(size=0.45, body="#8a7a64", wing="#6a5a48", head="#1e1a18", beak="cone", neck=0.6, leg=2, tail="long", crest="tuft"),
    "woodpecker": dict(size=0.5, body="#3a3a3a", wing="#2a2a2a", head="#c8321f", beak="long", neck=0.6, leg=2, tail="short", crest="tuft"),
    "nightingale": dict(size=0.45, body="#9a7a5a", wing="#7a5a3a", head="#9a7a5a", beak="cone", neck=0.6, leg=2, tail="long"),
    "quail":    dict(size=0.45, body="#9a7a54", wing="#7a5a3a", head="#7a5a3a", beak="cone", neck=0.4, leg=1.6, tail="short"),
    "partridge": dict(size=0.6, body="#a88a64", wing="#8a6a44", head="#c8843a", beak="cone", neck=0.8, leg=2.4, tail="short"),
    "chakor":   dict(size=0.6, body="#c8b8a0", wing="#a8987a", head="#e8dcc8", beak="cone", beak_color="#c8321f", neck=0.8, leg=2.4, tail="short"),
    "sarus":    dict(size=1.3, body="#b8bcc4", wing="#9aa0a8", head="#c8321f", beak="long", neck=10.0, leg=15, tail="short"),
    "cuckoo":   dict(size=0.55, body="#6a6a72", wing="#5a5a62", head="#6a6a72", beak="cone", neck=0.8, leg=2, tail="long"),
    "hawk":     dict(size=0.85, body="#7a5a3a", wing="#5a3c24", head="#9a7a54", beak="hook", neck=1.0, leg=3, tail="short"),
    "pelican":  dict(size=1.2, body="#f0ece4", wing="#d8d4cc", head="#f0ece4", beak="pouch", beak_color="#f2c23a", neck=3.0, leg=4, tail="short", swim=True),
    "bat":      dict(size=0.5, body="#2a2228", wing="#3a3038", head="#2a2228", beak="none", neck=0.2, leg=0.5, tail="none", bat=True),
    "butterfly": dict(size=0.3, body="#2a2228", wing="#f2a23a", head="#2a2228", beak="none", neck=0, leg=0, tail="none", butterfly=True),
}


def _b_body(sp, ppu, flying=False):
    s = sp["size"]
    p = Pen((-14, -16, 14, 18), ppu * s)
    c, hc = sp["body"], sp["head"]
    neck = sp["neck"]
    if sp.get("bat") or sp.get("butterfly"):
        p.ellipse(0, 0, 2.0, 1.0, fill=c)
        p.circle(2.2, -0.2, 0.9, fill=hc)
        return p.finish(seed=31)
    body = [(4.0, -2.4), (0.0, -3.4), (-4.6, -2.0), (-7.0, 0.4), (-4.0, 3.0), (1.0, 3.4), (4.6, 1.6)]
    if sp.get("owl"):
        body = [(3.0, -4.0), (-1.0, -4.6), (-3.6, -1.0), (-3.4, 4.0), (0.0, 6.0), (3.2, 4.0), (4.0, 0.0)]
    p.poly(body, fill=c, smooth=True)
    p.pattern(body, "scales", shade(c, -0.18), 1.3, 0.32, smooth=True)
    if not flying and sp["leg"] > 0 and not sp.get("swim"):
        for dx in (-0.6, 0.8):
            p.line([(dx, 2.8), (dx + 0.3, 2.8 + sp["leg"] * 0.5), (dx, 2.8 + sp["leg"])], "#c8843a", 0.36)
            p.line([(dx, 2.8 + sp["leg"]), (dx + 1.4, 3.0 + sp["leg"])], "#c8843a", 0.3)
    if sp.get("swim"):
        p.line([(-6.0, 2.4), (5.0, 2.4)], shade(c, -0.25), 0.3)
    # neck + head
    if sp.get("owl"):
        hx, hy = 0.6, -5.4
    else:
        ang = math.radians(-75 if neck > 5 else -45)
        hx, hy = 3.4 + math.cos(ang) * neck, -2.0 + math.sin(ang) * neck
        if neck > 0.5:
            pts = catmull([(3.0, -1.4), (3.4 + (hx - 3.4) * 0.3 + (1.2 if neck > 5 else 0), -2.0 + (hy + 2.0) * 0.5),
                           (hx, hy)], False, 8)
            for i in range(len(pts) - 1):
                p.poly(limb(pts[i], pts[i + 1], 1.7 - 0.6 * i / len(pts), 1.6 - 0.6 * i / len(pts)), fill=hc if neck > 5 else c)
    hr = 1.6 if not sp.get("owl") else 2.6
    if sp.get("crest") == "peacock":
        for dx in (-0.8, 0, 0.8):
            p.line([(hx, hy - 1.0), (hx + dx - 0.6, hy - 3.6)], hc, 0.14)
            p.circle(hx + dx - 0.6, hy - 3.8, 0.35, fill=hc)
    elif sp.get("crest") == "comb":
        p.poly([(hx - 0.8, hy - 1.2), (hx - 0.4, hy - 2.6), (hx + 0.2, hy - 1.6), (hx + 0.6, hy - 2.8), (hx + 1.0, hy - 1.2)],
               fill="#c8321f", smooth=True)
    elif sp.get("crest") == "tuft":
        p.poly([(hx - 1.2, hy - 0.6), (hx - 2.4, hy - 2.6), (hx + 0.2, hy - 1.2)], fill=hc)
    p.circle(hx, hy, hr, fill=hc)
    if sp.get("ruff"):
        p.ellipse(hx - 1.0, hy + 2.4, 2.4, 1.2, fill="#efe6d0")
    bc = sp.get("beak_color", "#e8b03a")
    bk = sp.get("beak", "cone")
    if bk == "hook":
        p.poly([(hx + hr * 0.7, hy - 0.6), (hx + hr + 1.8, hy - 0.2), (hx + hr + 1.6, hy + 1.2), (hx + hr * 0.7, hy + 0.6)],
               fill=bc, smooth=True)
    elif bk == "long":
        p.poly([(hx + hr * 0.8, hy - 0.4), (hx + hr + 4.6, hy + 0.3), (hx + hr * 0.8, hy + 0.5)], fill=bc)
    elif bk == "flat":
        p.poly([(hx + hr * 0.8, hy - 0.3), (hx + hr + 2.0, hy + 0.1), (hx + hr + 2.0, hy + 0.7), (hx + hr * 0.8, hy + 0.7)],
               fill=bc, smooth=True)
    elif bk == "horn":
        p.poly([(hx + hr * 0.7, hy - 1.0), (hx + hr + 3.6, hy + 0.2), (hx + hr * 0.7, hy + 0.8)], fill=bc)
        p.poly([(hx + hr * 0.4, hy - 1.6), (hx + hr + 2.4, hy - 1.2), (hx + hr * 0.7, hy - 0.8)], fill=shade(bc, -0.15))
    elif bk == "bent":
        p.poly([(hx + hr * 0.8, hy - 0.4), (hx + hr + 2.4, hy), (hx + hr + 2.2, hy + 1.6), (hx + hr * 0.8, hy + 0.6)],
               fill="#f2e2c0")
        p.poly([(hx + hr + 1.6, hy + 0.6), (hx + hr + 2.4, hy), (hx + hr + 2.2, hy + 1.6)], fill=INK)
    elif bk == "pouch":
        p.poly([(hx + hr * 0.8, hy - 0.4), (hx + hr + 5.0, hy + 0.2), (hx + hr + 1.6, hy + 2.6), (hx + hr * 0.8, hy + 1.0)],
               fill=bc, smooth=True)
    elif bk == "cone":
        p.poly([(hx + hr * 0.8, hy - 0.5), (hx + hr + 1.2, hy + 0.1), (hx + hr * 0.8, hy + 0.6)], fill=bc)
    if sp.get("ring"):
        p.line(arc_pts(hx, hy, hr * 1.02, hr * 1.02, 40, 140, 8), "#c8321f", 0.3)
    if sp.get("owl"):
        for ex in (hx - 0.9, hx + 1.1):
            p.circle(ex, hy - 0.2, 0.9, fill="#f2d36a", outline=INK, w=0.12)
            p.circle(ex + 0.1, hy - 0.2, 0.45, fill=INK)
    else:
        p.circle(hx + 0.4, hy - 0.3, 0.5, fill="#f6ecd6", outline=INK, w=0.1)
        p.circle(hx + 0.55, hy - 0.3, 0.26, fill=INK)
    return p.finish(seed=32, ow=0.26)


def _b_wing(sp, ppu, far=False):
    s = sp["size"]
    p = Pen((-14, -16, 4, 4), ppu * s)
    c = sp["wing"] if not far else shade(sp["wing"], -0.15)
    if sp.get("butterfly"):
        pts = [(0, 0), (-3, -6), (-7, -7), (-8, -4), (-5, -1), (-7, 2), (-4, 3), (0, 1)]
        p.poly(pts, fill=c, smooth=True)
        p.pattern(pts, "dots", "#2a2228", 1.4, 0.6, smooth=True)
        return p.finish(seed=33, ow=0.2)
    if sp.get("bat"):
        pts = [(0, 0), (-3, -6), (-8, -8), (-12, -6), (-10, -3), (-8, -2), (-6, 0), (-3, -1)]
        p.poly(pts, fill=c)
        return p.finish(seed=33, ow=0.2)
    pts = [(1.0, 0.2), (-1.4, -3.4), (-5.6, -7.0), (-11.4, -9.6), (-9.6, -6.6), (-12.0, -5.4), (-8.6, -3.4),
           (-10.0, -1.6), (-6.4, -0.6), (-6.8, 1.0), (-2.8, 1.4)]
    p.poly(pts, fill=c)
    p.poly([(1.0, 0.2), (-1.4, -3.4), (-5.6, -6.4), (-4.4, -2.4), (-1.6, -0.2)], fill=shade(c, 0.18), smooth=True)
    p.pattern([(1.0, 0.2), (-1.4, -3.4), (-5.6, -6.4), (-4.4, -2.4)], "scales", shade(c, -0.2), 1.0, 0.25)
    for k in range(5):
        p.line([(-3.0 - k * 1.6, -1.0 - k * 0.4), (-6.0 - k * 1.4, -4.0 - k * 1.0)], shade(c, -0.3), 0.14)
    return p.finish(seed=33, ow=0.24)


def _b_tail(sp, ppu):
    s = sp["size"]
    kind = sp.get("tail", "short")
    p = Pen((-30, -26, 4, 10), ppu * s)
    c = sp["wing"]
    if kind == "peacock":
        # long trailing train of eye-feathers (folded), painted like a Kalamkari motif
        base = (0, 0)
        for k in range(9):
            a = math.radians(180 + (k - 4) * 6)
            L = 22 + abs(k - 4) * -1.2
            tip = (math.cos(a) * L, math.sin(a) * L * 0.5 + 2)
            p.line([base, tip], "#2f6a3a", 0.3)
            p.ellipse(tip[0], tip[1], 1.9, 1.4, fill="#2f7a54")
            p.ellipse(tip[0] + 0.2, tip[1], 1.3, 1.0, fill="#d8b43a")
            p.ellipse(tip[0] + 0.3, tip[1], 0.8, 0.62, fill="#2a5ea8")
            p.circle(tip[0] + 0.4, tip[1], 0.32, fill="#14183a")
        p.poly([(0, -1.6), (-12, -2.4), (-22, 0.6), (-12, 3.0), (0, 1.6)], fill="#2f7a54", smooth=True)
        p.pattern([(0, -1.6), (-12, -2.4), (-22, 0.6), (-12, 3.0), (0, 1.6)], "dots", "#d8b43a", 1.6, 0.5, smooth=True)
    elif kind == "long":
        p.poly([(0.6, -0.6), (-9.0, -2.0), (-13.0, -1.0), (-9.0, 1.0), (0.6, 0.8)], fill=c, smooth=True)
    elif kind == "forked":
        p.poly([(0.6, -0.6), (-6.0, -2.4), (-4.4, 0), (-6.0, 2.0), (0.6, 0.8)], fill=c)
    elif kind == "rooster":
        for k, col in enumerate(("#1f4a3a", "#2a2626", "#1f4a3a")):
            p.poly([(0.6, -0.6), (-4.0, -5.0 - k), (-7.0, -3.0 - k), (-5.0, 0.0), (0.6, 0.8)], fill=col, smooth=True)
    elif kind == "none":
        p.circle(0, 0, 0.1, fill=c)
    else:
        p.poly([(0.6, -0.8), (-4.0, -1.4), (-4.6, 0.6), (0.6, 1.0)], fill=c, smooth=True)
    return p.finish(seed=34, ow=0.24)


def build_bird(spec, ppu=9.0):
    sp = dict(BIRDS.get(spec.get("base", spec.get("id")), BIRDS["sparrow"]))
    sp.update({k: v for k, v in spec.items() if v is not None})
    rig = Rig(spec.get("id", "bird"), ppu)
    rig.meta = {"spec": sp, "kind": "bird"}
    s = sp["size"]
    body = _b_body(sp, ppu)
    rig.add(Part("body", body, None, (0, 0), z=10))
    rig.add(Part("wing_b", _b_wing(sp, ppu, far=True), "body", (0.4 * s, -1.6 * s), z=2, rest=38))
    rig.add(Part("wing_f", _b_wing(sp, ppu), "body", (0.0, -1.4 * s), z=12, rest=42))
    rig.add(Part("tail", _b_tail(sp, ppu), "body", (-6.0 * s, 0.0), z=8))
    rig.meta["flying_body"] = _b_body(sp, ppu, flying=True)
    rig.ground = (2.8 + sp["leg"]) * s if not sp.get("swim") else 2.4 * s
    rig.extent = (-34 * s, -30 * s, 22 * s, 22 * s)
    rig.anchors = {"head": ("body", (2.0 * s, -6.0 * s))}
    rig.meta["scale"] = float(spec.get("scale", 1.0)) * BIRD_K
    return rig


# =========================================================================== serpents & water beasts

def build_serpent(spec, ppu=9.0):
    c = spec.get("color", "#3f7a48")
    hoods = int(spec.get("hoods", 1))
    L = float(spec.get("length", 1.0))
    p = Pen((-30 * L, -42, 30 * L, 8), ppu)
    # coils on the ground
    for k, (cx, rx) in enumerate(((-12 * L, 10 * L), (4 * L, 12 * L), (-4 * L, 9 * L))):
        p.ellipse(cx, 2.0 - k * 2.4, rx, 3.2, fill=shade(c, -0.08 * k))
        p.pattern(arc_pts(cx, 2.0 - k * 2.4, rx, 3.2, 0, 360, 24), "scales", shade(c, 0.3), 1.6, 0.4)
    # rising neck
    path = catmull([(8 * L, 0), (12 * L, -8), (10 * L, -16), (12 * L, -22)], False, 8)
    for i in range(len(path) - 1):
        w = 5.0 - 1.6 * i / len(path)
        p.poly(limb(path[i], path[i + 1], w, w), fill=c)
    for i in range(1, len(path) - 1, 2):
        x, y = path[i]
        p.line([(x - 1.6, y), (x + 1.6, y)], "#e8d8a0", 0.6)
    hx, hy = path[-1]
    for k in range(hoods):
        a = -90 + (k - (hoods - 1) / 2) * (34 if hoods > 1 else 0)
        cx = hx + math.cos(math.radians(a)) * (7.5 if hoods > 1 else 0)
        cy = hy - 2 + math.sin(math.radians(a)) * (7.5 if hoods > 1 else 0) + (5 if hoods > 1 else 0)
        pts = rot([(cx - 3.0, cy + 3.6), (cx - 3.4, cy - 1.0), (cx, cy - 4.2), (cx + 3.4, cy - 1.0), (cx + 3.0, cy + 3.6)],
                  a + 90, cx, cy)
        p.poly(pts, fill=shade(c, 0.05), smooth=True)
        p.pattern(pts, "scales", shade(c, 0.35), 1.1, 0.35, smooth=True)
        p.circle(cx + 0.8, cy - 1.0, 0.45, fill="#f2d36a")
        p.circle(cx + 0.9, cy - 1.0, 0.2, fill=INK)
        p.line([(cx + 2.6, cy + 0.2), (cx + 4.2, cy + 0.6), (cx + 4.8, cy + 0.2)], "#c8321f", 0.2)
    spr = p.finish(seed=41)
    rig = Rig(spec.get("id", "naga"), ppu)
    rig.meta = {"spec": spec, "kind": "serpent", "scale": float(spec.get("scale", 1.0)) * 1.6}
    rig.add(Part("body", spr, None, (0, 0), z=10))
    rig.ground = 5.2
    rig.extent = (-34 * L - 4, -48, 34 * L + 4, 12)
    rig.anchors = {"head": ("body", (hx, hy - 6))}
    return rig


def build_fish(spec, ppu=9.0):
    c = spec.get("color", "#e8833a")
    S = float(spec.get("size", 1.0))
    p = Pen((-16, -8, 14, 8), ppu * S)
    body = [(10, 0), (5, -4.2), (-3, -4.0), (-9, -0.6), (-9, 0.6), (-3, 4.0), (5, 4.2)]
    p.poly(body, fill=c, smooth=True)
    p.pattern(body, "scales", shade(c, -0.25), 1.6, 0.4, smooth=True)
    p.poly([(-8, 0), (-14, -5), (-12.6, 0), (-14, 5)], fill=shade(c, 0.15))
    p.poly([(0, -4), (-3, -7), (-5, -3.6)], fill=shade(c, 0.15))
    p.circle(6.4, -1.0, 0.9, fill="#f6ecd6", outline=INK, w=0.12)
    p.circle(6.6, -1.0, 0.45, fill=INK)
    spr = p.finish(seed=42)
    rig = Rig(spec.get("id", "fish"), ppu)
    rig.meta = {"spec": spec, "kind": "fish", "scale": float(spec.get("scale", 1.0)) * 1.6}
    rig.add(Part("body", spr, None, (0, 0), z=10))
    rig.ground = 0
    rig.extent = (-18 * S, -10 * S, 16 * S, 10 * S)
    rig.anchors = {}
    return rig


def build_creature(spec, ppu=9.0, use_cache=True):
    """Dispatch on spec['kind'] in {quadruped, bird, serpent, fish}. Cached."""
    key = stable_hash({"spec": spec, "ppu": ppu, "v": FAUNA_VERSION})
    cp = CACHE_DIR / "rigs" / f"fauna_{spec.get('id', 'x')}_{key}.pkl"
    if use_cache and cp.exists():
        try:
            with open(cp, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    kind = spec.get("kind", "quadruped")
    if kind == "bird":
        rig = build_bird(spec, ppu)
    elif kind == "serpent":
        rig = build_serpent(spec, ppu)
    elif kind == "fish":
        rig = build_fish(spec, ppu)
    else:
        rig = build_quadruped(spec, ppu)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with open(cp, "wb") as f:
            pickle.dump(rig, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return rig
