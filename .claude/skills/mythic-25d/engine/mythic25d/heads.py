"""Folk-art profile heads (facing right) + headgear.

Head-local units: pivot (0,0) = neck base; the face looks toward +x;
the skull top sits near y = -14.  All drawing happens on a `Pen`.
"""
from __future__ import annotations

import math

from .gfx import arc_pts, bezier, catmull, limb, move, rot
from .util import mix, rgb, shade

INK = "ink"


# =========================================================================== face parts

def _eye(p, cx, cy, w=3.4, h=1.0, style="almond", iris="black", white="#f6ecd6"):
    if style == "round":  # rakshasa / animal bulging eye
        p.ellipse(cx, cy, w * 0.42, w * 0.42, fill=white, outline=INK, w=0.28)
        p.circle(cx + w * 0.1, cy, w * 0.2, fill=iris)
        p.circle(cx + w * 0.05, cy - w * 0.08, w * 0.06, fill="#fff6e0")
        return
    x0, x1 = cx - w / 2, cx + w / 2
    up = bezier((x0, cy), (x0 + w * 0.3, cy - h * 1.15), (x1 - w * 0.25, cy - h * 1.1), (x1, cy - 0.05), 14)
    lo = bezier((x1, cy - 0.05), (x1 - w * 0.3, cy + h * 0.75), (x0 + w * 0.3, cy + h * 0.7), (x0, cy), 14)
    p.poly(up + lo, fill=white)
    p.circle(cx + w * 0.14, cy - h * 0.2, h * 0.62, fill=iris)
    p.circle(cx + w * 0.2, cy - h * 0.38, h * 0.16, fill="#fff6e0")
    p.line(up, INK, 0.36)
    p.line(lo, INK, 0.2)
    # kohl flick toward the ear
    p.line([(x0, cy), (x0 - w * 0.33, cy + 0.12), (x0 - w * 0.48, cy - 0.15)], INK, 0.26, smooth=True)


def _brow(p, cx, cy, w=3.6, k=0.7, angry=False):
    if angry:
        p.line([(cx - w / 2, cy - k * 0.9), (cx, cy - k * 0.2), (cx + w / 2, cy + k * 0.4)], INK, 0.46, smooth=True)
    else:
        p.line([(cx - w / 2, cy), (cx - w * 0.05, cy - k), (cx + w / 2, cy - k * 0.35)], INK, 0.36, smooth=True)


def _ear(p, x, y, skin, s=1.0):
    pts = [(x + 0.9 * s, y - 1.7 * s), (x - 0.7 * s, y - 1.9 * s), (x - 1.25 * s, y - 0.2 * s),
           (x - 0.6 * s, y + 1.6 * s), (x + 0.6 * s, y + 1.4 * s), (x + 0.2 * s, y)]
    p.poly(pts, fill=shade(skin, -0.06), smooth=True)
    p.line([(x + 0.2 * s, y - 1.1 * s), (x - 0.6 * s, y - 0.9 * s), (x - 0.5 * s, y + 0.6 * s)], INK, 0.22, smooth=True)


def _kundal(p, x, y, color="gold", r=1.0, kind="ring"):
    if kind == "jhumka":
        p.line([(x, y - 0.4), (x, y + 0.6)], "gold_dk", 0.18)
        p.poly([(x - 0.9 * r, y + 1.9 * r), (x, y + 0.4), (x + 0.9 * r, y + 1.9 * r)], fill=color, smooth=True)
        for k in range(5):
            p.circle(x - 0.8 * r + k * 0.4 * r, y + 2.1 * r, 0.18 * r, fill="cream")
        return
    p.circle(x, y + r, r, outline=color, w=0.42)
    p.circle(x, y + 2 * r, 0.34 * r, fill="vermilion")


def _tilak(p, kind, x, y):
    if kind == "vaishnav":
        p.line([(x - 0.18, y + 1.2), (x - 0.25, y - 1.4)], "#f4ead2", 0.28)
        p.line([(x + 0.12, y + 1.0), (x + 0.02, y - 1.4)], "vermilion", 0.32)
    elif kind == "shaiva":
        for k in range(3):
            p.line([(x - 0.9, y - 0.8 + k * 0.55), (x + 0.15, y - 0.8 + k * 0.55)], "#f4ead2", 0.2)
        p.circle(x - 0.25, y - 0.25, 0.22, fill="vermilion")
    elif kind == "bindi":
        p.circle(x, y, 0.38, fill="vermilion")
    elif kind == "dot":
        p.circle(x, y, 0.3, fill="vermilion")


# =========================================================================== head shapes

HUMAN_MALE = [(-1.8, -2.4), (-4.7, -4.8), (-5.8, -8.8), (-4.6, -12.6), (-0.8, -14.3), (2.9, -13.2),
              (4.4, -11.0), (4.6, -9.5), (5.05, -8.7), (6.25, -6.75), (6.45, -6.35), (5.4, -5.95),
              (5.5, -5.3), (5.05, -4.85), (5.25, -4.45), (4.6, -3.35), (3.3, -2.45), (1.8, -2.55)]
HUMAN_FEMALE = [(-1.6, -2.6), (-4.4, -4.9), (-5.4, -8.8), (-4.3, -12.4), (-0.8, -13.9), (2.7, -12.9),
                (4.1, -10.8), (4.3, -9.4), (4.65, -8.6), (5.6, -6.9), (5.7, -6.5), (5.0, -6.1),
                (5.05, -5.45), (4.7, -5.0), (4.85, -4.6), (4.2, -3.5), (3.0, -2.75), (1.7, -2.7)]


def _human(p, s, female=False):
    skin = s["skin"]
    pts = HUMAN_FEMALE if female else HUMAN_MALE
    p.poly([(-2.3, 0.7), (-2.0, -3.6), (2.2, -3.6), (2.6, 0.7)], fill=skin)  # neck
    p.poly(pts, fill=skin, smooth=True, n=8)
    # cheek warmth
    p.ellipse(2.4, -5.6, 1.6, 1.0, fill=mix(skin, "#d0603e", 0.12))
    _eye(p, 2.55, -8.3, 3.3 if not female else 3.5, 0.95 if not female else 1.05,
         "round" if s.get("eye") == "round" else "almond",
         iris=s.get("iris", "black"))
    _brow(p, 2.6, -9.75, 3.5, 0.6, angry=s.get("angry", False))
    # nostril + lips
    p.line([(5.4, -6.35), (5.0, -6.2)], INK, 0.2)
    lip = "#b8402e" if not female else "#c4363a"
    if female:
        p.poly([(4.95, -5.35), (4.4, -5.1), (4.95, -4.75)], fill=lip, smooth=True)
    else:
        p.line([(5.15, -5.0), (4.55, -4.95)], shade(skin, -0.45), 0.24)
    if s.get("fangs"):
        p.poly([(4.9, -4.95), (4.6, -3.7), (4.4, -4.95)], fill="#f6efdf", outline=INK, w=0.12)
        p.poly([(4.0, -4.95), (3.8, -5.9), (3.6, -4.95)], fill="#f6efdf", outline=INK, w=0.12)
    # ear + earring
    _ear(p, -1.2, -7.6, skin)
    _kundal(p, -1.25, -5.9, s.get("metal", "gold"), 0.9, "jhumka" if female else "ring")
    if female:
        p.circle(5.25, -6.15, 0.55, outline="gold", w=0.2)  # nath
        p.circle(5.6, -5.75, 0.16, fill="#f6efdf")
    # mustache
    m = s.get("mustache")
    if m:
        col = s.get("beard_color", "ink")
        if m == "curl":
            p.line([(5.15, -5.65), (4.0, -5.55), (3.0, -5.9), (2.6, -6.6), (3.05, -6.85)], col, 0.5, smooth=True)
        elif m == "big":
            p.line([(5.2, -5.6), (3.6, -5.2), (2.2, -5.8), (1.4, -7.2), (1.9, -7.6)], col, 0.85, smooth=True)
        else:
            p.line([(5.15, -5.65), (3.6, -5.45), (3.0, -5.7)], col, 0.45, smooth=True)
    tl = s.get("tilak")
    if tl:
        _tilak(p, tl, 4.05 if not female else 3.8, -11.3 if tl != "bindi" else -10.3)
    if s.get("third_eye"):
        p.ellipse(3.95, -11.7, 0.32, 0.6, fill="vermilion", outline=INK, w=0.1)


def _beard(p, s, long=True):
    col = s.get("beard_color", "white")
    if long:
        pts = [(0.6, -5.8), (2.6, -4.2), (4.6, -3.9), (5.2, -2.6), (4.6, 1.0), (3.6, 5.5), (2.0, 9.0),
               (0.6, 6.0), (-0.6, 2.0), (-0.9, -2.5)]
    else:
        pts = [(0.4, -6.0), (2.6, -4.2), (4.7, -4.0), (5.0, -2.8), (3.9, -1.2), (1.6, -1.0), (-0.3, -3.0)]
    p.poly(pts, fill=col, smooth=True)
    for k in range(5 if long else 3):
        x = 0.8 + k * 0.85
        p.line([(x, -3.5), (x + 0.4, -0.5), (x - 0.1 + k * 0.1, 3 if long else -1.6)], shade(col, -0.28), 0.14, smooth=True)
    p.line([(5.15, -5.65), (3.8, -5.45), (2.6, -5.5), (1.6, -4.6)], col, 0.55, smooth=True)


def _hair_back(p, s, female=False):
    col = s.get("hair_color", "black")
    style = s.get("hair", "long")
    if style in (None, "none", "bald"):
        return
    if female:
        pts = [(-0.5, -14.2), (-4.6, -12.9), (-6.2, -9.0), (-6.2, -4.0), (-7.0, 2.5), (-7.6, 9.0),
               (-5.8, 12.0), (-4.2, 8.0), (-3.6, 2.0), (-2.6, -3.2)]
    elif style == "short":
        pts = [(-0.5, -14.4), (-4.8, -12.8), (-6.0, -9.0), (-5.6, -5.4), (-3.5, -4.4), (-2.0, -6.8)]
    else:
        pts = [(-0.5, -14.4), (-4.8, -12.9), (-6.3, -9.0), (-6.6, -4.0), (-7.6, 1.8), (-8.0, 6.0),
               (-6.2, 6.8), (-4.6, 3.2), (-3.6, -1.6), (-2.2, -3.4)]
    p.poly(pts, fill=col, smooth=True)
    hl = shade(col, 0.22)
    for k in range(3):
        p.line([(-3.0 - k * 0.9, -12.5), (-5.0 - k * 0.6, -8), (-5.4 - k * 0.7, -2), (-6 - k * 0.5, 3)], hl, 0.16,
               smooth=True)


def _hair_front(p, s, female=False):
    col = s.get("hair_color", "black")
    if s.get("hair") in ("bald",):
        return
    # hairline band visible under crowns
    pts = [(-4.9, -11.6), (-2.0, -13.6), (2.6, -13.3), (4.1, -11.6), (2.8, -12.1), (0.4, -11.8), (-2.2, -10.4),
           (-3.6, -8.6), (-4.6, -9.4)]
    p.poly(pts, fill=col, smooth=True)


# ---------------------------------------------------------------- animal heads

def _monkey(p, s):
    skin = s["skin"]
    face = s.get("face", shade(skin, -0.05))
    muzzle = s.get("muzzle", "#f0dcb0")
    p.poly([(-2.4, 0.7), (-2.2, -3.8), (2.2, -3.8), (2.7, 0.7)], fill=skin)
    head = [(-1.6, -2.4), (-4.9, -5.0), (-6.0, -9.2), (-4.4, -13.2), (-0.4, -14.6), (3.2, -13.4),
            (4.8, -11.2), (5.2, -9.4), (6.7, -8.2), (7.6, -6.2), (7.2, -4.0), (5.4, -2.6), (2.8, -2.0)]
    p.poly(head, fill=skin, smooth=True, n=8)
    # facial disc + muzzle (the iconic cream mouth of the vanara puppets)
    p.poly([(1.0, -11.6), (4.6, -11.4), (5.6, -9.2), (4.6, -6.8), (2.0, -6.0), (0.8, -8.4)], fill=face, smooth=True)
    p.poly([(3.0, -7.9), (5.8, -8.9), (7.7, -7.1), (7.7, -4.7), (6.0, -2.9), (3.6, -3.0), (2.6, -5.2)],
           fill=muzzle, smooth=True)
    p.line([(7.4, -5.2), (5.6, -5.0), (4.2, -5.6)], INK, 0.3, smooth=True)  # mouth
    p.circle(7.2, -7.2, 0.35, fill=INK)  # nostril
    p.line([(3.0, -10.6), (4.4, -11.2), (5.5, -10.3)], INK, 0.55, smooth=True)  # brow ridge
    _eye(p, 3.6, -9.3, 2.4, 0.85)
    p.line([(3.0, -6.4), (4.0, -4.0)], shade(muzzle, -0.25), 0.18)
    _ear(p, -1.6, -8.0, skin, 1.25)
    _kundal(p, -1.6, -5.9, "gold", 1.0)
    if s.get("tilak"):
        _tilak(p, s["tilak"], 4.0, -12.2)


def _bear(p, s):
    skin = s["skin"]
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.4, -3.8), (2.8, 0.7)], fill=skin)
    head = [(-1.8, -2.0), (-5.2, -5.0), (-6.4, -9.6), (-4.6, -13.6), (-0.4, -14.8), (3.4, -13.2),
            (5.4, -10.6), (7.6, -8.6), (8.4, -6.8), (7.4, -5.2), (5.0, -3.6), (2.4, -1.8)]
    p.poly(head, fill=skin, smooth=True)
    p.poly([(4.6, -9.2), (7.7, -8.5), (8.3, -6.8), (6.8, -5.3), (4.6, -5.8)], fill=shade(skin, 0.25), smooth=True)
    p.circle(8.1, -7.4, 0.55, fill=INK)
    p.circle(-2.6, -13.2, 1.6, fill=skin, outline=INK, w=0.2)
    p.circle(-2.6, -13.2, 0.8, fill=shade(skin, 0.25))
    _eye(p, 3.4, -9.6, 1.6, 0.7, "round", iris=INK, white="#e9dcc0")
    beard = s.get("beard_color", "white")
    if s.get("beard"):
        p.poly([(1.0, -6.4), (5.6, -4.6), (5.0, -1.0), (2.6, 3.0), (0.4, 1.0), (-0.8, -3.0)], fill=beard, smooth=True)
        p.line([(6.4, -5.8), (4.2, -5.0), (2.6, -6.2)], beard, 0.5, smooth=True)
    p.pattern(head, "speckle", shade(skin, 0.18), spacing=1.4, size=0.25, smooth=True)


def _elephant(p, s):
    skin = s["skin"]
    ear_in = s.get("ear_inner", "#d98e8a")
    # big fan ear behind
    ear = [(-1.5, -14.0), (-7.2, -14.6), (-10.5, -10.0), (-10.2, -2.8), (-6.8, 1.6), (-2.4, 0.8), (-1.2, -4.0)]
    p.poly(ear, fill=shade(skin, -0.08), smooth=True)
    p.poly(move(rot([(x * 0.78, y * 0.78) for x, y in ear], 0), -1.3, -1.6), fill=ear_in, smooth=True)
    p.pattern(move([(x * 0.78, y * 0.78) for x, y in ear], -1.3, -1.6), "dots", "#f2d2a8", 1.3, 0.32, smooth=True)
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.6, -3.8), (3.0, 0.7)], fill=skin)
    head = [(-2.0, -2.0), (-4.0, -8.0), (-3.6, -13.6), (0.0, -16.6), (4.2, -15.6), (6.4, -12.6), (7.0, -9.2),
            (6.0, -6.0), (3.8, -3.0)]
    p.poly(head, fill=skin, smooth=True)
    # trunk: tapered chain curling forward and down
    path = catmull([(5.6, -8.6), (7.4, -5.0), (7.6, -0.8), (6.0, 2.6), (3.8, 3.6), (2.8, 2.2), (3.6, 1.0)], False, 6)
    n = len(path)
    for i in range(n - 1):
        w = 3.4 - 2.4 * i / n
        p.poly(limb(path[i], path[i + 1], w, w * 0.95), fill=skin)
    for i in range(2, n - 2, 2):
        x, y = path[i]
        p.line([(x - 1.2, y - 0.4), (x + 1.2, y + 0.4)], shade(skin, -0.3), 0.14)
    # tusk (Ekadanta: one broken)
    p.poly([(5.4, -5.6), (8.6, -4.6), (9.4, -5.4), (6.0, -6.6)], fill="#f6efdf", smooth=True, outline=INK, w=0.14)
    _eye(p, 3.8, -10.4, 1.9, 0.6)
    p.line([(2.8, -11.6), (4.6, -11.8)], INK, 0.3)
    _tilak(p, s.get("tilak", "shaiva"), 5.8, -12.6)


def _lion(p, s):
    skin = s["skin"]
    mane = s.get("mane", shade(skin, -0.28))
    spikes = []
    for k in range(17):
        a = math.radians(-250 + k * 14)
        r = 9.8 if k % 2 == 0 else 7.4
        spikes.append((-0.8 + math.cos(a) * r, -7.8 + math.sin(a) * r))
    p.poly(spikes, fill=mane)
    p.poly([(x * 0.8 - 0.3, -7.8 + (y + 7.8) * 0.8) for x, y in spikes], fill=shade(mane, 0.15))
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.4, -3.8), (2.8, 0.7)], fill=skin)
    head = [(-2.0, -2.6), (-4.0, -7.0), (-3.2, -12.0), (0.6, -13.6), (4.2, -12.4), (5.8, -10.0), (7.8, -8.6),
            (8.2, -6.6), (7.6, -4.6), (6.4, -3.0), (4.0, -1.8), (1.0, -1.6)]
    p.poly(head, fill=skin, smooth=True)
    p.poly([(5.6, -6.0), (8.0, -5.4), (7.4, -3.6), (5.4, -3.2)], fill="#8e2a1c", smooth=True)  # open mouth
    p.poly([(7.6, -5.5), (7.2, -4.4), (6.9, -5.5)], fill="#f6efdf")
    p.poly([(6.0, -3.4), (6.3, -4.4), (6.6, -3.4)], fill="#f6efdf")
    p.circle(7.9, -7.4, 0.5, fill=INK)
    _eye(p, 4.0, -9.8, 2.0, 0.7, "round", iris="#9a1d10", white="#f2d36a")
    p.line([(2.8, -11.0), (4.0, -10.8), (5.4, -10.0)], INK, 0.5, smooth=True)
    for k in range(3):
        p.line([(6.2, -6.6 + k * 0.4), (8.6 + k * 0.3, -6.9 + k * 0.6)], INK, 0.12)


def _eagle(p, s):
    skin = s["skin"]
    feather = s.get("feather", "#d1662c")
    crest = [(-1.0, -13.0), (-6.0, -16.8), (-4.2, -13.6), (-8.0, -14.0), (-5.0, -11.8), (-8.4, -10.6),
             (-4.6, -9.6), (-2.0, -10.2)]
    p.poly(crest, fill=feather)
    p.poly([(-2.4, 0.7), (-2.2, -3.8), (2.2, -3.8), (2.6, 0.7)], fill=skin)
    head = [(-2.0, -2.6), (-4.8, -6.0), (-5.0, -10.4), (-2.0, -13.8), (2.4, -13.6), (5.0, -11.0), (5.6, -8.0),
            (4.2, -5.0), (1.2, -2.8)]
    p.poly(head, fill=skin, smooth=True)
    p.pattern(head, "scales", shade(skin, -0.25), 1.4, 0.35, smooth=True)
    beak = [(4.4, -10.2), (8.4, -9.6), (10.0, -7.8), (9.4, -5.4), (8.6, -6.8), (6.8, -7.0), (4.6, -6.6)]
    p.poly(beak, fill=s.get("beak", "#e8b03a"), smooth=False, outline=INK, w=0.18)
    p.line([(5.0, -7.6), (8.2, -7.8)], INK, 0.18)
    _eye(p, 3.0, -9.4, 2.0, 0.8, "round", iris=INK, white="#f6d24a")


def _boar(p, s):
    skin = s["skin"]
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.4, -3.8), (2.8, 0.7)], fill=skin)
    head = [(-2.0, -2.4), (-4.8, -7.0), (-3.6, -12.6), (0.4, -14.0), (4.0, -11.8), (7.4, -9.6), (10.0, -8.6),
            (10.2, -6.2), (7.6, -4.6), (4.0, -2.4)]
    p.poly(head, fill=skin, smooth=True)
    p.ellipse(10.0, -7.4, 0.8, 1.4, fill=shade(skin, 0.2), outline=INK, w=0.15)
    p.poly([(7.0, -5.2), (8.6, -7.8), (9.0, -7.2), (7.8, -4.8)], fill="#f6efdf", outline=INK, w=0.12)
    p.poly([(-1.2, -12.2), (-3.4, -16.2), (0.6, -13.4)], fill=shade(skin, -0.1), outline=INK, w=0.15)
    _eye(p, 2.8, -9.6, 1.7, 0.6)
    p.pattern(head, "stripes", shade(skin, -0.12), 1.1, 0.12, smooth=True)


def _horse(p, s):
    skin = s["skin"]
    mane = s.get("mane", "#3a2818")
    p.poly([(-5.8, -12.0), (-3.0, -14.6), (-1.0, -12.0), (-4.8, -2.0), (-7.0, 1.0)], fill=mane, smooth=True)
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.4, -3.8), (2.8, 0.7)], fill=skin)
    head = [(-2.0, -2.4), (-3.8, -8.0), (-1.4, -13.4), (2.2, -13.2), (5.4, -9.6), (9.4, -6.6), (10.4, -4.6),
            (9.2, -3.0), (5.6, -2.8), (2.0, -1.8)]
    p.poly(head, fill=skin, smooth=True)
    p.poly([(-1.0, -12.8), (0.2, -16.2), (1.4, -12.8)], fill=skin, outline=INK, w=0.15)
    p.circle(9.4, -5.2, 0.45, fill=INK)
    p.line([(10.0, -3.6), (8.2, -3.6)], INK, 0.2)
    _eye(p, 2.8, -9.6, 1.8, 0.65)


def _buffalo(p, s):
    skin = s["skin"]
    horn = s.get("horn", "#e8dcc0")
    p.poly([(-3.0, -12.0), (-9.0, -14.0), (-12.5, -18.5), (-10.0, -21.0), (-9.5, -17.0), (-5.0, -14.2), (-1.0, -13.4)],
           fill=horn, smooth=True, outline=INK, w=0.15)
    p.poly([(-2.6, 0.7), (-2.4, -3.8), (2.4, -3.8), (2.8, 0.7)], fill=skin)
    head = [(-2.0, -2.4), (-4.6, -7.4), (-3.0, -12.8), (1.0, -13.8), (4.4, -11.4), (7.8, -8.0), (8.6, -5.2),
            (6.6, -3.2), (3.0, -2.0)]
    p.poly(head, fill=skin, smooth=True)
    p.poly([(2.6, -12.6), (8.0, -15.0), (11.0, -19.4), (12.6, -17.0), (9.4, -12.4), (4.4, -10.6)], fill=horn,
           smooth=True, outline=INK, w=0.15)
    p.ellipse(7.8, -5.0, 1.0, 1.2, fill=shade(skin, 0.25))
    p.circle(8.0, -5.4, 0.3, fill=INK)
    _eye(p, 3.2, -9.0, 2.0, 0.8, "round", iris="#9a1d10", white="#f2d36a")


def _fishhead(p, s):
    _human(p, s)


HEADS = {"human": _human, "monkey": _monkey, "bear": _bear, "elephant": _elephant, "lion": _lion,
         "eagle": _eagle, "boar": _boar, "horse": _horse, "buffalo": _buffalo}


# =========================================================================== headgear

def _kirita(p, s, tiers=6, h=2.15, w0=9.2, top=1.6, base=-12.4, dx=-0.3):
    gold = s.get("crown_color", "gold")
    gd = shade(gold, -0.32)
    gem = s.get("gem", "vermilion")
    # plume at back (red/green feather tuft — very characteristic)
    if s.get("plume", True):
        pl = s.get("plume_color", "vermilion")
        y = base - tiers * h * 0.55
        p.poly([(-3.0 + dx, y + 1.0), (-7.4 + dx, y - 1.8), (-8.8 + dx, y - 4.6), (-6.0 + dx, y - 3.2), (-5.4 + dx, y - 5.4),
                (-3.4 + dx, y - 1.6)], fill=pl, smooth=True)
        p.poly([(-3.4 + dx, y + 0.2), (-6.6 + dx, y - 2.0), (-5.2 + dx, y - 0.6)], fill="leaf", smooth=True)
    # side flare (makara) behind ears
    p.poly([(-4.6 + dx, base + 0.4), (-7.0 + dx, base - 1.6), (-6.2 + dx, base + 1.8), (-4.4 + dx, base + 2.4)], fill=gold,
           smooth=True)
    y = base
    for k in range(tiers):
        f0 = 1 - k / (tiers + 0.6)
        f1 = 1 - (k + 1) / (tiers + 0.6)
        a0, a1 = w0 * f0 / 2, w0 * f1 / 2
        cx = dx + k * 0.05
        quad = [(cx - a0, y), (cx - a1 * 1.08, y - h * 0.55), (cx - a1, y - h), (cx + a1, y - h),
                (cx + a1 * 1.08, y - h * 0.55), (cx + a0, y)]
        p.poly(quad, fill=gold if k % 2 == 0 else shade(gold, 0.1), smooth=False)
        p.line([(cx - a0, y), (cx + a0, y)], gd, 0.24)
        for j in range(max(1, int(a0 * 1.2))):
            xx = cx - a0 + (j + 0.5) * (2 * a0) / max(1, int(a0 * 1.2))
            p.circle(xx, y - h * 0.45, 0.17, fill=gd if k % 2 else "cream")
        y -= h
    p.circle(dx + tiers * 0.05, y - 0.7, 0.95, fill=gold, outline=gd, w=0.15)
    p.poly([(dx - 0.5, y - 1.3), (dx, y - top - 1.6), (dx + 0.5, y - 1.3)], fill=gold)
    # crown band with gem row
    band = [(-4.9 + dx, base + 1.5), (4.6 + dx, base + 1.3), (4.4 + dx, base - 0.3), (-4.8 + dx, base - 0.2)]
    p.poly(band, fill=gold)
    p.line([(-4.8 + dx, base + 0.65), (4.5 + dx, base + 0.5)], gd, 0.18)
    for k in range(4):
        p.circle(-3.4 + dx + k * 2.4, base + 0.6, 0.38, fill=gem if k % 2 == 0 else "emerald")
    p.circle(3.6 + dx, base - 0.8, 0.9, fill=gold, outline=gd, w=0.14)
    p.circle(3.6 + dx, base - 0.8, 0.42, fill=gem)


def _peacock_feather(p, x, y, ang=-20, L=8.0):
    pts = rot([(x, y), (x, y - L)], ang, x, y)
    p.line(pts, "#3b5a2a", 0.22)
    tip = pts[1]
    p.ellipse(tip[0], tip[1], 1.7, 2.3, fill="#2f7a54")
    p.ellipse(tip[0], tip[1] + 0.2, 1.2, 1.6, fill="#d8b43a")
    p.ellipse(tip[0], tip[1] + 0.35, 0.8, 1.05, fill="#2a5ea8")
    p.ellipse(tip[0], tip[1] + 0.45, 0.42, 0.55, fill="#14183a")


def _jata(p, s, shiva=False):
    col = s.get("hair_color", "#5a3a24" if not shiva else "#4a3022")
    # matted locks falling down the back
    for k in range(4):
        x = -4.6 - k * 0.9
        p.poly(limb((x + 1.0, -11.0), (x - 1.4 - k * 0.3, 2.0 + k * 1.6), 1.6, 1.0), fill=shade(col, -0.05 * k))
    # tall coiled bun: stacked rings
    for k in range(5):
        y = -12.6 - k * 2.0
        w = 3.9 - k * 0.42
        p.ellipse(-0.9 + k * 0.12, y, w, 1.35, fill=col if k % 2 == 0 else shade(col, 0.12))
        p.line(arc_pts(-0.9 + k * 0.12, y, w * 0.8, 0.8, 200, 340, 10), shade(col, 0.32), 0.2)
    p.ellipse(-0.3, -22.4, 1.6, 1.4, fill=shade(col, 0.1))
    p.line([(-4.8, -11.6), (-1.0, -12.4), (2.8, -11.6)], "#8a4b2c", 0.7, smooth=True)  # rudraksha band
    for k in range(6):
        p.circle(-4.4 + k * 1.4, -11.9 + (0.25 if k in (0, 5) else -0.2), 0.36, fill="#6a2f1c")
    if shiva:
        # crescent moon + Ganga spout
        p.poly(arc_pts(3.0, -17.8, 2.1, 2.1, 110, 330, 14) + arc_pts(3.7, -18.3, 1.6, 1.7, 330, 110, 14)[::-1],
               fill="#f3ecd2")
        p.line([(-0.6, -23.4), (-1.8, -26.0), (-0.6, -28.2), (-1.2, -30.0)], "#9ad0e6", 0.7, smooth=True)
        p.circle(-1.2, -30.2, 0.75, fill="#d4eef6")


def _female_crown(p, s):
    gold = s.get("crown_color", "gold")
    gd = shade(gold, -0.32)
    p.poly([(-4.6, -11.8), (-4.4, -14.6), (-2.6, -13.6), (-1.6, -17.0), (0.0, -14.4), (1.4, -17.6), (2.6, -14.0),
            (3.8, -15.6), (4.2, -11.6)], fill=gold)
    p.line([(-4.5, -12.1), (4.1, -11.9)], gd, 0.3)
    for k, x in enumerate((-1.6, 1.4)):
        p.circle(x, -15.4 + (0.3 if k else 0), 0.45, fill="vermilion")
    p.circle(0.0, -12.8, 0.5, fill="emerald")


def _bun(p, s):
    col = s.get("hair_color", "black")
    p.circle(-5.2, -9.4, 2.6, fill=col)
    for k in range(7):
        a = math.radians(200 + k * 22)
        p.circle(-5.2 + math.cos(a) * 2.6, -9.4 + math.sin(a) * 2.6, 0.48, fill="#f8f2e2")


def _veil(p, s):
    c = s.get("veil_color", s.get("saree", ["maroon"])[0] if isinstance(s.get("saree"), list) else "maroon")
    pts = [(-0.6, -15.0), (3.6, -13.8), (4.6, -11.4), (2.4, -12.4), (-1.6, -12.0), (-4.2, -9.0), (-5.0, -2.0),
           (-7.0, 6.0), (-9.4, 8.0), (-8.6, -2.0), (-7.0, -10.6), (-4.6, -14.0)]
    p.poly(pts, fill=c, smooth=True)
    p.line([(3.6, -13.6), (-0.8, -14.6), (-5.0, -12.0), (-7.4, -6.0), (-8.6, 2.0), (-9.0, 7.6)], "gold", 0.5, smooth=True)


def _turban(p, s):
    c = s.get("turban_color", "saffron")
    pts = [(-5.4, -10.0), (-5.8, -14.0), (-3.0, -17.0), (1.4, -17.2), (4.4, -15.0), (4.6, -11.4), (0.0, -12.2)]
    p.poly(pts, fill=c, smooth=True)
    for k in range(3):
        p.line([(-5.4, -11.2 - k * 1.8), (0.0, -13.0 - k * 1.6), (4.4, -12.0 - k * 1.6)], shade(c, -0.25), 0.25,
               smooth=True)
    p.circle(2.6, -14.6, 0.7, fill="vermilion", outline="gold", w=0.2)
    p.poly([(2.4, -15.0), (1.6, -19.6), (3.4, -16.0)], fill="#f6efdf", smooth=True)


def _horns(p, s):
    hc = s.get("horn_color", "#e6dcc6")
    p.poly([(-2.0, -13.4), (-5.6, -17.6), (-5.0, -21.6), (-3.8, -18.6), (-0.6, -14.6)], fill=hc, smooth=True,
           outline=INK, w=0.15)
    p.poly([(1.8, -13.6), (4.4, -17.4), (6.8, -19.8), (5.8, -16.4), (3.6, -13.0)], fill=hc, smooth=True,
           outline=INK, w=0.15)


def _spiky(p, s):
    gold = s.get("crown_color", "#c8902c")
    pts = [(-4.8, -11.6)]
    for k in range(7):
        x = -4.4 + k * 1.45
        pts += [(x, -14.0 - (2.8 if k % 2 == 0 else 1.6)), (x + 0.72, -13.6)]
    pts += [(4.6, -11.4)]
    p.poly(pts, fill=gold)
    p.line([(-4.8, -12.2), (4.6, -12.0)], shade(gold, -0.35), 0.4)
    p.circle(0.0, -13.2, 0.7, fill="#3a8a3a")
    p.circle(0.0, -13.2, 0.3, fill="#f6efdf")


def _helmet(p, s):
    c = s.get("crown_color", "#9a9488")
    p.poly([(-5.0, -10.8), (-5.4, -14.4), (-2.0, -16.8), (2.6, -16.0), (4.6, -12.6), (4.0, -10.6)], fill=c, smooth=True)
    p.line([(-5.0, -11.4), (4.2, -11.2)], "gold", 0.5)
    p.poly([(-0.4, -16.6), (-1.6, -20.6), (0.8, -16.4)], fill="vermilion", smooth=True)


def _shikha(p, s):
    col = s.get("hair_color", "black")
    p.line([(-2.8, -13.4), (-4.4, -15.0), (-5.8, -14.4), (-6.6, -12.4)], col, 0.7, smooth=True)


def _hoods(p, s, n=5):
    hood_c = s.get("hood_color", "#2f6a4a")
    for k in range(n):
        a = -90 + (k - (n - 1) / 2) * (100 / max(1, n - 1) if n > 1 else 0)
        cx = -1.0 + math.cos(math.radians(a)) * 9.0
        cy = -10.0 + math.sin(math.radians(a)) * 9.0
        pts = rot([(cx - 2.2, cy + 3.0), (cx - 2.6, cy - 1.0), (cx, cy - 3.4), (cx + 2.6, cy - 1.0), (cx + 2.2, cy + 3.0)],
                  a + 90, cx, cy)
        p.poly(pts, fill=hood_c, smooth=True)
        p.pattern(pts, "scales", shade(hood_c, 0.3), 0.9, 0.3, smooth=True)
        p.circle(cx + 0.6, cy - 0.6, 0.35, fill="#f2d36a")


def _flames(p, s):
    for k, (x, h) in enumerate(((-4.0, 6.0), (-2.0, 8.5), (0.2, 7.0), (2.4, 9.0), (4.0, 5.5))):
        pts = [(x - 1.6, -12.0), (x - 0.4, -12.0 - h * 0.6), (x, -12.0 - h), (x + 0.6, -12.0 - h * 0.5), (x + 1.6, -12.0)]
        p.poly(pts, fill="#e8521e", smooth=True)
        p.poly([(x - 0.8, -12.0), (x, -12.0 - h * 0.6), (x + 0.8, -12.0)], fill="#ffcf4a", smooth=True)


def _sun_rays(p, s):
    for k in range(16):
        a = math.radians(k * 22.5)
        p.poly([(-0.4 + math.cos(a) * 8.5, -9 + math.sin(a) * 8.5),
                (-0.4 + math.cos(a + 0.12) * 11.5, -9 + math.sin(a + 0.12) * 11.5),
                (-0.4 + math.cos(a + 0.24) * 8.5, -9 + math.sin(a + 0.24) * 8.5)], fill="#f0a52a")
    p.circle(-0.4, -9, 8.6, fill="#f4c046")


def draw_back_headgear(p, s):
    """Things that go BEHIND the head shape."""
    hg = s.get("crown")
    if hg == "hoods":
        _hoods(p, s, s.get("hoods", 5))
    elif hg == "sun":
        _sun_rays(p, s)


def draw_headgear(p, s):
    hg = s.get("crown", "kirita")
    if hg in ("kirita", "kirita_tall"):
        _kirita(p, s, tiers=s.get("tiers", 6))
    elif hg == "kirita_low":
        _kirita(p, s, tiers=3, h=2.0, w0=9.0)
    elif hg == "peacock":
        _kirita(p, s, tiers=3, h=2.0, w0=8.8, **{})
        _peacock_feather(p, -1.0, -18.0, -25, 6.0)
    elif hg == "jata":
        _jata(p, s)
    elif hg == "jata_shiva":
        _jata(p, s, shiva=True)
    elif hg == "tiara":
        _female_crown(p, s)
    elif hg == "bun":
        _bun(p, s)
    elif hg == "veil":
        _veil(p, s)
    elif hg == "turban":
        _turban(p, s)
    elif hg == "horns":
        _horns(p, s)
        _spiky(p, s)
    elif hg == "spiky":
        _spiky(p, s)
    elif hg == "helmet":
        _helmet(p, s)
    elif hg == "shikha":
        _shikha(p, s)
    elif hg == "flames":
        _flames(p, s)
    elif hg == "sun":
        _kirita(p, s, tiers=3, h=2.0, w0=9.0, base=-12.4)
    elif hg == "hoods":
        _kirita(p, s, tiers=4, h=2.0, w0=9.0)


def draw_head(p, s):
    """Full head incl. hair & headgear. s = resolved head spec."""
    kind = s.get("head", "human")
    female = s.get("female", False)
    draw_back_headgear(p, s)
    if kind == "human":
        if s.get("crown") not in ("veil",):
            _hair_back(p, s, female)
        if s.get("crown") == "bun" or (female and s.get("crown") in ("tiara",)):
            _bun(p, s)
        _human(p, s, female)
        if s.get("beard"):
            _beard(p, s, long=s.get("beard") != "short")
        if s.get("crown") not in ("jata", "jata_shiva", "bald", "shikha", "hoods") and s.get("hair") != "bald":
            _hair_front(p, s, female)
    else:
        HEADS.get(kind, _human)(p, s)
    if kind in ("lion",) and s.get("crown") in (None, "none"):
        return
    draw_headgear(p, s)
