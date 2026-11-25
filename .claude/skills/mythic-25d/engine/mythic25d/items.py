"""Held attributes & weapons (ayudha).  Local units: grip = (0,0); the item
extends along +y (the direction the forearm points), so a raised forearm
holds a mace head-up.  Each entry: draw fn, pen bounds, flags."""
from __future__ import annotations

import math

from .gfx import arc_pts, bezier, catmull, limb, rot
from .util import shade

INK = "ink"


def gada(p):
    p.poly(limb((0, -3.2), (0, 9.5), 1.0, 1.1), fill="#8a5a2a")
    for y in (-1.5, 2.0, 5.5):
        p.poly(limb((0, y), (0, y + 0.7), 1.5, 1.5), fill="gold")
    p.circle(0, -3.8, 0.9, fill="gold")
    p.circle(0, 12.6, 3.6, fill="gold")
    for k in range(-2, 3):
        p.line(arc_pts(0, 12.6, 3.6 * abs(math.cos(k * 0.5)) if k else 0.2, 3.5, -90, 90, 12) if k else [(0, 9.1), (0, 16.1)],
               shade("gold", -0.35), 0.18)
    p.ellipse(0, 12.6, 3.6, 1.0, outline=shade("gold", -0.35), w=0.2)
    p.poly([(-0.6, 16.0), (0, 18.0), (0.6, 16.0)], fill="gold")
    p.circle(-1.2, 11.4, 0.7, fill="#fff0b8")


def bow(p):
    # grip (hand) at origin; limbs curve back toward the archer (-x), string behind
    pts = bezier((-3.6, -16), (1.2, -8), (1.2, 8), (-3.6, 16), 30)
    for i in range(len(pts) - 1):
        w = 1.25 - abs(i - 15) * 0.03
        p.poly(limb(pts[i], pts[i + 1], w, w), fill="#9a5a26")
    for i in range(3, 28, 5):
        x, y = pts[i]
        p.line([(x - 0.6, y), (x + 0.6, y)], "gold", 0.3)
    p.line([(-3.8, -16), (-3.8, 16)], "#efe3c4", 0.14)
    for y in (-16, 16):
        p.circle(-3.6, y, 0.6, fill="gold")
    p.poly(limb((0.0, -1.6), (0.0, 1.6), 1.7, 1.7), fill="gold")


def arrow(p):
    p.line([(0, -10), (0, 13)], "#c8a060", 0.32)
    p.poly([(-0.9, 12.6), (0, 15.8), (0.9, 12.6)], fill="#b8b8b0", outline=INK, w=0.1)
    for s in (-1, 1):
        p.poly([(0, -9.8), (s * 1.1, -10.8), (s * 1.0, -7.8), (0, -7.2)], fill="vermilion")


def trishul(p):
    p.poly(limb((0, -10), (0, 15), 0.7, 0.7), fill="#a8a49a")
    p.poly([(-0.5, 15), (0, 22.4), (0.5, 15)], fill="#c9c6bb", outline=INK, w=0.1)
    for s in (-1, 1):
        prong = catmull([(0, 14.6), (s * 2.8, 15.2), (s * 3.3, 17.6), (s * 2.5, 20.6)], False, 6)
        p.line(prong, "#c9c6bb", 0.6)
    p.poly(limb((-1.6, 14.4), (1.6, 14.4), 0.8, 0.8), fill="gold")
    # damru tied below prongs
    p.poly([(-1.4, 10.8), (1.4, 10.8), (0.2, 12.4), (1.4, 14.0), (-1.4, 14.0), (-0.2, 12.4)], fill="#b8742c",
           outline=INK, w=0.1)


def chakra(p):
    cx, cy, R = 0, 5.4, 4.0
    for k in range(16):
        a = math.radians(k * 22.5)
        p.poly([(cx + math.cos(a - 0.12) * R, cy + math.sin(a - 0.12) * R),
                (cx + math.cos(a) * (R + 1.5), cy + math.sin(a) * (R + 1.5)),
                (cx + math.cos(a + 0.12) * R, cy + math.sin(a + 0.12) * R)], fill="#f09a2a")
    p.circle(cx, cy, R, fill="gold")
    p.circle(cx, cy, R * 0.72, fill="#f4c96a")
    for k in range(8):
        a = math.radians(k * 45)
        p.line([(cx, cy), (cx + math.cos(a) * R * 0.72, cy + math.sin(a) * R * 0.72)], shade("gold", -0.4), 0.28)
    p.circle(cx, cy, 0.9, fill="vermilion")


def shankh(p):
    body = [(-0.6, 0.6), (2.6, 1.4), (4.4, 3.6), (4.0, 6.4), (2.0, 7.4), (-0.4, 6.4), (-2.0, 4.4), (-2.6, 2.0)]
    p.poly(body, fill="#f6efdf", smooth=True)
    p.poly([(0.2, 3.0), (2.8, 3.4), (3.0, 5.4), (1.0, 5.6)], fill="#f2b38a", smooth=True)
    p.line(arc_pts(-0.4, 2.0, 1.6, 1.2, 180, 520, 24), shade("#f6efdf", -0.3), 0.18)


def padma(p):
    p.line([(0, -2), (0.4, 6), (0, 8)], "#4f7d3a", 0.45, smooth=True)
    cx, cy = 0, 9.4
    for k, a in enumerate((-60, -30, 0, 30, 60)):
        pet = rot([(cx, cy + 0.6), (cx - 1.1, cy - 1.4), (cx, cy - 3.6), (cx + 1.1, cy - 1.4)], a + 180, cx, cy)
        p.poly(pet, fill="#ea8fa3" if k % 2 else "#f2b2bf", smooth=True)
    p.circle(cx, cy, 0.9, fill="#f2c94a")


def damru(p):
    p.poly([(-1.8, 1.0), (1.8, 1.0), (0.3, 3.4), (1.8, 5.8), (-1.8, 5.8), (-0.3, 3.4)], fill="#b8742c", outline=INK,
           w=0.12)
    p.line([(-1.8, 1.0), (1.8, 1.0)], "gold", 0.4)
    p.line([(-1.8, 5.8), (1.8, 5.8)], "gold", 0.4)
    p.line([(0.3, 3.4), (2.6, 4.0)], "#efe3c4", 0.1)
    p.circle(2.7, 4.1, 0.35, fill=INK)


def khadga(p):
    p.poly(limb((0, -2.4), (0, 0.8), 0.9, 0.9), fill="gold")
    p.poly(limb((-1.8, 1.0), (1.8, 1.0), 0.7, 0.7), fill="gold")
    blade = [(-0.7, 1.4), (0.8, 1.4), (1.4, 9.0), (0.6, 15.6), (-0.2, 16.6), (-0.4, 10.0)]
    p.poly(blade, fill="#c9c6bb", smooth=False, outline=INK, w=0.12)
    p.line([(0.1, 2.0), (0.4, 13.0)], "#f6f2e8", 0.16)


def dhal(p):
    p.circle(0, 0, 4.6, fill="#7a4a24")
    p.circle(0, 0, 4.0, fill="#9a5e2c")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p.circle(math.cos(a) * 2.2, math.sin(a) * 2.2, 0.55, fill="gold")
    p.circle(0, 0, 0.8, fill="gold")


def vajra(p):
    p.poly(limb((0, -1.4), (0, 1.4), 1.1, 1.1), fill="gold")
    for s in (-1, 1):
        y0 = 1.4 * s
        for dx in (-1.2, 0, 1.2):
            p.line(catmull([(0, y0), (dx * 1.3, y0 + s * 2.0), (dx * 0.4, y0 + s * 4.4)], False, 6), "gold", 0.4)
        p.circle(0, y0 + s * 4.6, 0.5, fill="gold")


def kamandalu(p):
    p.line(arc_pts(0, 1.8, 1.4, 1.8, 180, 360, 12), "#6a3c1c", 0.35)
    p.poly([(-2.6, 2.4), (2.6, 2.4), (3.0, 5.6), (1.6, 7.6), (-1.6, 7.6), (-3.0, 5.6)], fill="#9a5a2a", smooth=True)
    p.poly([(2.4, 3.4), (4.6, 2.6), (4.8, 3.0), (2.8, 4.4)], fill="#9a5a2a")
    p.line([(-2.8, 4.6), (2.8, 4.6)], "gold", 0.3)


def mala(p):
    pts = arc_pts(0, 3.6, 1.8, 3.6, -90, 270, 22)
    for x, y in pts:
        p.circle(x, y, 0.42, fill="#6a2f1c")
    p.circle(0, 7.6, 0.6, fill="vermilion")


def pothi(p):
    p.poly([(-4.4, 0.6), (4.4, 0.6), (4.4, 2.8), (-4.4, 2.8)], fill="#e6cf8e", outline=INK, w=0.14)
    for x in (-2.2, 2.2):
        p.line([(x, 0.6), (x, 2.8)], "vermilion", 0.18)
    p.line([(-3.8, 1.7), (3.8, 1.7)], shade("#e6cf8e", -0.3), 0.08)


def bansuri(p):
    p.poly(limb((-1.0, 0), (-1.0, 14), 0.75, 0.75), fill="#c89a4a")
    for y in (4, 5.6, 7.2, 8.8, 10.4):
        p.circle(-1.0, y, 0.18, fill=INK)
    p.poly(limb((-1.0, 1.5), (-1.0, 2.3), 0.95, 0.95), fill="vermilion")


def veena(p):
    p.poly(limb((0, -8), (0, 16), 1.1, 1.0), fill="#8a5426")
    p.circle(0, 17.4, 3.6, fill="#b8742c")
    p.circle(0, 17.4, 2.6, fill="#d29242")
    p.circle(0.4, -7.6, 2.4, fill="#b8742c")
    for x in (-0.3, 0.3):
        p.line([(x, -8), (x, 15)], "#efe3c4", 0.07)
    for y in range(-6, 14, 3):
        p.line([(-0.9, y), (0.9, y)], "gold", 0.16)


def pasha(p):
    p.line(arc_pts(0, 4.8, 3.2, 4.4, -80, 260, 30), "#c08a3a", 0.42)
    p.line([(0, 0.2), (0.4, 0.8)], "#c08a3a", 0.42)


def ankusha(p):
    p.poly(limb((0, -2), (0, 10), 0.6, 0.6), fill="#c9c6bb")
    p.line(catmull([(0, 10), (0.6, 12.6), (-0.6, 13.6), (-2.2, 12.4)], False, 6), "#c9c6bb", 0.55)
    p.poly([(0.0, 9.6), (0.6, 12.0), (-0.5, 12.0)], fill="#c9c6bb")


def parashu(p):
    p.poly(limb((0, -6), (0, 14), 0.8, 0.8), fill="#8a5a2a")
    blade = [(0.3, 10.0), (4.6, 8.8), (5.6, 12.0), (4.6, 15.4), (0.3, 14.0)]
    p.poly(blade, fill="#c9c6bb", smooth=True, outline=INK, w=0.12)
    p.line([(4.8, 9.4), (5.4, 12.0), (4.8, 14.8)], "#f6f2e8", 0.2, smooth=True)


def hala(p):
    p.poly(limb((0, -8), (0, 13), 0.8, 0.8), fill="#8a5a2a")
    p.poly([(0, 12), (3.4, 14.4), (2.0, 15.4), (-0.4, 13.2)], fill="#c9c6bb", outline=INK, w=0.12)


def danda(p):
    p.poly(limb((0, -22), (0, 34), 0.8, 0.8), fill="#8a5a2a")
    p.circle(0, -22.4, 0.9, fill="#8a5a2a")


def shakti(p):
    p.poly(limb((0, -20), (0, 20), 0.6, 0.6), fill="#8a5a2a")
    p.poly([(0, 19), (-1.6, 23), (0, 28), (1.6, 23)], fill="#c9c6bb", outline=INK, w=0.12)
    p.poly(limb((-1.1, 19.4), (1.1, 19.4), 0.6, 0.6), fill="gold")


def dhwaja(p):
    p.poly(limb((0, -16), (0, 26), 0.5, 0.5), fill="#8a5a2a")
    p.poly([(0, 25), (9, 22.6), (0, 19.6)], fill="saffron")
    p.circle(0, 26.4, 0.6, fill="gold")


def chhatra(p):
    p.poly(limb((0, -4), (0, 18), 0.45, 0.45), fill="#8a5a2a")
    dome = arc_pts(0, 18.8, 8.6, 4.2, 180, 360, 24)
    p.poly(dome + [(8.6, 18.8), (-8.6, 18.8)], fill="vermilion")
    for k in range(9):
        x = -8 + k * 2
        p.poly([(x - 1, 18.8), (x, 20.0), (x + 1, 18.8)], fill="gold")
    p.circle(0, 14.2, 0.7, fill="gold")


def diya(p):
    p.poly([(-2.2, 1.0), (2.2, 1.0), (1.2, 2.6), (-1.2, 2.6)], fill="#b8742c", smooth=True)
    p.poly([(-0.7, 1.0), (0, -2.2), (0.7, 1.0)], fill="#ffcf4a", smooth=True)


def kalash(p):
    p.poly([(-2.6, -1.2), (2.6, -1.2), (3.2, -4.0), (1.4, -6.2), (-1.4, -6.2), (-3.2, -4.0)], fill="#d39b3a", smooth=True)
    for k in range(5):
        p.poly([(-1.6 + k * 0.8, -6.2), (-1.2 + k * 0.8, -8.4), (-0.8 + k * 0.8, -6.2)], fill="leaf")
    p.circle(0, -8.6, 1.3, fill="#a8742c")


def modak(p):
    p.poly([(-3.0, -0.6), (3.0, -0.6), (2.0, -2.4), (-2.0, -2.4)], fill="gold")
    for x in (-1.6, 0, 1.6):
        p.poly([(x - 0.9, -2.4), (x, -4.4), (x + 0.9, -2.4)], fill="#f3e6c6", smooth=True)


def flower(p):
    p.line([(0, 0), (0.3, 4)], "#4f7d3a", 0.3)
    for a in range(0, 360, 60):
        p.circle(0.3 + math.cos(math.radians(a)) * 0.9, 4.8 + math.sin(math.radians(a)) * 0.9, 0.7, fill="vermilion")
    p.circle(0.3, 4.8, 0.5, fill="gold")


def chamara(p):
    p.poly(limb((0, -2), (0, 5), 0.6, 0.6), fill="gold")
    p.poly([(-1.4, 5), (1.4, 5), (2.0, 10), (0, 13), (-2.0, 10)], fill="#f6efdf", smooth=True)


def bag(p):
    p.line([(0, 0), (0, 2)], "#8a5a2a", 0.3)
    p.poly([(-2.0, 2.0), (2.0, 2.0), (2.6, 6.4), (-2.6, 6.4)], fill="#c08a3a", smooth=True)


def sudarshan(p):
    chakra(p)


def mirror(p):
    p.poly(limb((0, 0), (0, 3), 0.6, 0.6), fill="gold")
    p.ellipse(0, 6, 2.4, 3.0, fill="gold")
    p.ellipse(0, 6, 1.8, 2.4, fill="#cfe3ea")


ITEMS = {
    # name: (fn, bounds(x0,y0,x1,y1), world_upright_angle or None, joint offset)
    "gada": (gada, (-5, -6, 5, 19), None, (0, 0)),
    "bow": (bow, (-5, -17.4, 2.4, 17.4), None, (0, 0)),
    "arrow": (arrow, (-2, -11, 2, 16.5), None, (0, 0)),
    "trishul": (trishul, (-4.4, -11, 4.4, 23), None, (0, 0)),
    "chakra": (chakra, (-6, -1, 6, 11), None, (0, 0)),
    "sudarshan": (sudarshan, (-6, -1, 6, 11), None, (0, 0)),
    "shankh": (shankh, (-3.4, -0.5, 5.2, 8.4), None, (0, 0)),
    "padma": (padma, (-4.6, -2.5, 4.6, 13.6), None, (0, 0)),
    "damru": (damru, (-2.4, 0, 3.4, 6.6), None, (0, 0)),
    "khadga": (khadga, (-2.6, -3, 2.6, 17.4), None, (0, 0)),
    "sword": (khadga, (-2.6, -3, 2.6, 17.4), None, (0, 0)),
    "dhal": (dhal, (-5.2, -5.2, 5.2, 5.2), None, (0, 0)),
    "shield": (dhal, (-5.2, -5.2, 5.2, 5.2), None, (0, 0)),
    "vajra": (vajra, (-2.6, -6, 2.6, 6), None, (0, 0)),
    "kamandalu": (kamandalu, (-3.6, -0.4, 5.4, 8.4), 0.0, (0, 0)),
    "mala": (mala, (-2.6, -0.6, 2.6, 8.6), 0.0, (0, 0)),
    "pothi": (pothi, (-5, 0, 5, 3.4), None, (0, 0)),
    "bansuri": (bansuri, (-2, -1, 0.2, 15), None, (0, 0)),
    "veena": (veena, (-4.2, -10.6, 4.2, 21.4), None, (0, 0)),
    "pasha": (pasha, (-3.8, -0.4, 3.8, 9.8), 0.0, (0, 0)),
    "ankusha": (ankusha, (-3, -2.6, 1.6, 14.4), None, (0, 0)),
    "parashu": (parashu, (-1, -6.6, 6.4, 16.2), None, (0, 0)),
    "hala": (hala, (-1, -8.6, 4.2, 16), None, (0, 0)),
    "danda": (danda, (-1.4, -23.6, 1.4, 34.6), 180.0, (0, 0)),
    "shakti": (shakti, (-2.2, -20.6, 2.2, 28.6), 180.0, (0, 0)),
    "spear": (shakti, (-2.2, -20.6, 2.2, 28.6), 180.0, (0, 0)),
    "dhwaja": (dhwaja, (-1, -16.6, 9.6, 27.2), 180.0, (0, 0)),
    "flag": (dhwaja, (-1, -16.6, 9.6, 27.2), 180.0, (0, 0)),
    "chhatra": (chhatra, (-9.2, -4.6, 9.2, 20.6), 180.0, (0, 0)),
    "diya": (diya, (-2.6, -2.8, 2.6, 3.2), 0.0, (0, -0.6)),
    "kalash": (kalash, (-3.6, -10.2, 3.6, -0.6), 0.0, (0, 0)),
    "modak": (modak, (-3.4, -5, 3.4, 0), 0.0, (0, 0)),
    "flower": (flower, (-1.6, -0.4, 2.2, 6.4), None, (0, 0)),
    "chamara": (chamara, (-2.6, -2.6, 2.6, 13.6), None, (0, 0)),
    "bag": (bag, (-3, -0.4, 3, 7), 0.0, (0, 0)),
    "mirror": (mirror, (-2.8, -0.4, 2.8, 9.4), None, (0, 0)),
}


# extra rotation of the item relative to the forearm (deg)
ITEM_REST = {"bow": 90.0, "pothi": 0.0, "dhal": 0.0}


def build_item(name, ppu, finish_kw=None):
    from .gfx import Pen
    fn, bounds, world, off = ITEMS[name]
    pen = Pen(bounds, ppu)
    fn(pen)
    from .gfx import ITEM_STYLE
    spr = pen.finish(**{**ITEM_STYLE, **(finish_kw or {})})
    return spr, world, off
