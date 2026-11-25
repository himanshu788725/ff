"""Parametric 2.5D painted jointed-puppet builder.

`build_character(spec)` turns a catalog entry (see data/characters.json) into a
`Rig` of finished paper-cut sprites: torso, head (+extra heads), arms (+extra
arms) with held items, legs / seated lap / saree skirt / serpent or fish tail,
monkey tail, wings, halo.  Rigs are cached on disk.
"""
from __future__ import annotations

import math
import pickle

from .gfx import CHAR_STYLE, Pen, arc_pts, catmull, limb, rot, move
from .util import mix


def fin(p, **kw):
    """Finish a puppet part with the thick-outline, bevelled 2.5D cut-out style."""
    return p.finish(**{**CHAR_STYLE, **kw})
from .heads import draw_head
from .items import ITEMS, ITEM_REST, build_item
from .rig import Part, Rig
from .util import code_version, CACHE_DIR, mix, rgb, shade, stable_hash

BUILD_VERSION = code_version("puppet", "heads", "items", "gfx")
INK = "ink"

BUILDS = {
    #          shoulder chest waist hip   upper-arm w   fore w     belly  leg-w  scale
    "hero":   dict(sw=9.4, cw=8.6, ww=6.2, hw=7.1, ua=(5.1, 3.9), fa=(3.8, 2.9), belly=0.0, lw=5.4, s=1.0),
    "slim":   dict(sw=8.6, cw=7.8, ww=5.8, hw=6.6, ua=(4.5, 3.5), fa=(3.4, 2.6), belly=0.0, lw=4.9, s=0.98),
    "heavy":  dict(sw=9.8, cw=9.6, ww=8.6, hw=8.2, ua=(5.6, 4.4), fa=(4.2, 3.2), belly=4.2, lw=6.0, s=1.0),
    "female": dict(sw=7.6, cw=7.4, ww=5.0, hw=7.6, ua=(4.0, 3.2), fa=(3.1, 2.4), belly=0.0, lw=4.6, s=0.94),
    "old":    dict(sw=8.2, cw=7.6, ww=5.8, hw=6.6, ua=(4.2, 3.3), fa=(3.2, 2.5), belly=0.6, lw=4.6, s=0.96),
    "child":  dict(sw=7.2, cw=7.0, ww=6.0, hw=6.4, ua=(4.0, 3.2), fa=(3.2, 2.5), belly=1.4, lw=4.6, s=0.62),
    "giant":  dict(sw=10.6, cw=10.2, ww=8.8, hw=8.6, ua=(6.0, 4.8), fa=(4.6, 3.6), belly=3.0, lw=6.6, s=1.22),
}

DEFAULTS = {
    "head": "human", "female": False, "build": "hero", "skin": "skin_tan", "hair": "long", "hair_color": "black",
    "crown": "kirita", "mustache": "curl", "beard": None, "tilak": None, "third_eye": False,
    "lower": "dhoti", "dhoti": ["vermilion", "dots", "cream"], "sash": "mustard", "top": "bare",
    "metal": "gold", "janeu": False, "necklace": True, "pearls": False, "armor": None,
    "saree": ["maroon", "floral", "gold"], "choli": "mustard",
    "items": {}, "arms": 2, "extra_items": [], "heads": [], "tail": False, "wings": None,
    "halo": False, "halo_color": "gold", "snake": False, "mundamala": False, "rudraksha": False,
    "eye": "almond", "fangs": False, "angry": False, "scale": 1.0, "tongue": False,
}


def resolve(spec: dict) -> dict:
    s = dict(DEFAULTS)
    s.update({k: v for k, v in spec.items() if v is not None or k in ("beard", "mustache")})
    if s["female"]:
        s.setdefault("crown", "tiara")
        if spec.get("mustache") is None:
            s["mustache"] = None
        if s["build"] == "hero":
            s["build"] = "female"
        if s["lower"] == "dhoti" and "lower" not in spec:
            s["lower"] = "saree"
    return s


# =========================================================================== torso

def torso_outline(b, female=False):
    sw, cw, ww, hw, bl = b["sw"], b["cw"], b["ww"], b["hw"], b["belly"]
    pts = [(2.4, -40.4), (sw - 1.2, -38.9), (sw, -36.2), (sw - 0.7, -31.6), (cw, -27.2),
           (ww + 0.4 + bl * 0.55, -18.0), (ww + bl, -10.5), (hw + bl * 0.3, -3.4), (hw - 0.4, 1.8),
           (-hw + 0.4, 1.8), (-hw - bl * 0.1, -3.4), (-ww - bl * 0.35, -10.5), (-ww - 0.4 - bl * 0.2, -18.0),
           (-cw, -27.2), (-sw + 0.7, -31.6), (-sw, -36.2), (-sw + 1.2, -38.9), (-2.4, -40.4)]
    if female:
        pts[4] = (cw + 0.6, -28.0)
        pts[13] = (-cw - 0.2, -28.0)
    return pts


def luminance(c):
    r, g, b_, _ = rgb(c)
    return (0.299 * r + 0.587 * g + 0.114 * b_) / 255.0


def body_line(skin):
    return mix(skin, "#f4dca0", 0.62) if luminance(skin) < 0.5 else shade(skin, -0.42)


def build_torso(s, b, ppu):
    p = Pen((-16, -46, 16, 6), ppu)
    skin = s["skin"]
    female = s["female"] or s["build"] == "female"
    pts = torso_outline(b, female)
    p.poly(pts, fill=skin, smooth=True, n=8)
    metal = s["metal"]
    sw, ww = b["sw"], b["ww"]
    if female:
        choli = s["choli"]
        band = [(-b["cw"] - 0.3, -33.8), (b["cw"] + 0.3, -33.8), (b["cw"] + 0.8, -27.6), (3.6, -25.4), (0, -26.6),
                (-3.6, -25.4), (-b["cw"] - 0.4, -27.6)]
        p.poly(band, fill=choli, smooth=True, n=6)
        p.pattern(band, "dots", shade(choli, 0.45), 1.3, 0.3, smooth=True)
        p.line([(-b["cw"] - 0.4, -27.6), (-3.6, -25.4), (0, -26.6), (3.6, -25.4), (b["cw"] + 0.8, -27.6)], metal, 0.45,
               smooth=True)
        # pallu drape across chest
        sc = s["saree"][0] if isinstance(s["saree"], list) else s["saree"]
        drape = [(-sw + 0.6, -38.6), (-sw + 4.2, -39.2), (ww + 1.2, -17.0), (ww + 0.8, -11.6), (ww - 2.8, -12.6)]
        p.poly(drape, fill=sc, smooth=False)
        p.pattern(drape, "floral", shade(sc, 0.45), 1.6, 0.42)
        p.line([(-sw + 4.2, -39.2), (ww + 1.2, -17.0)], metal, 0.55)
        p.line([(-sw + 0.6, -38.6), (ww - 2.8, -12.6)], metal, 0.4)
        p.circle(0.6, -12.0, 0.35, fill=shade(skin, -0.4))
    else:
        if s.get("armor"):
            ac = s["armor"]
            plate = [(-b["cw"] + 0.6, -36.0), (b["cw"] - 0.6, -36.0), (b["cw"] - 0.2, -27.0), (ww + 0.2, -14.0),
                     (-ww - 0.2, -14.0), (-b["cw"] + 0.2, -27.0)]
            p.poly(plate, fill=ac, smooth=True, n=6)
            p.pattern(plate, "scales", shade(ac, -0.35), 1.6, 0.5, smooth=True)
            p.line(catmull(plate, True, 6) + [catmull(plate, True, 6)[0]], metal, 0.4)
        else:
            # pectorals, collarbones, abdomen, navel — light gold lines on dark skin (reference), ink on light skin
            line = body_line(skin)
            p.line([(-5.6, -37.0), (-1.2, -36.0)], line, 0.18)
            p.line([(1.8, -36.0), (6.2, -37.0)], line, 0.18)
            p.line(arc_pts(-3.6, -30.4, 3.2, 1.8, 20, 160, 12), line, 0.24)
            p.line(arc_pts(3.6, -30.4, 3.2, 1.8, 20, 160, 12), line, 0.24)
            p.circle(-3.6, -29.4, 0.3, fill=line)
            p.circle(3.8, -29.4, 0.3, fill=line)
            if b["belly"] > 2:
                p.line(arc_pts(1.0 + b["belly"] * 0.3, -14.0, ww + b["belly"] * 0.6, 5.6, 25, 155, 14), line, 0.22)
            else:
                p.line([(0.2, -25.0), (0.4, -17.0)], line, 0.18)
                for k in range(3):
                    p.line([(-2.2, -24.0 + k * 3.0), (-0.4, -23.6 + k * 3.0)], line, 0.15)
                    p.line([(1.0, -23.6 + k * 3.0), (2.8, -24.0 + k * 3.0)], line, 0.15)
            p.circle(0.6 + b["belly"] * 0.3, -10.6, 0.45, fill=line)
            if s["build"] == "old":
                for k in range(4):
                    p.line(arc_pts(-3.4, -33.0 + k * 1.6, 2.8, 0.8, 20, 160, 8), line, 0.12)
                    p.line(arc_pts(3.6, -33.0 + k * 1.6, 2.8, 0.8, 20, 160, 8), line, 0.12)
    if s.get("tiger_top"):
        pass
    # sacred thread
    if s.get("janeu"):
        p.line([(-sw + 1.6, -37.6), (-1.0, -22.0), (ww + 0.6, -7.0)], "#f3ead2", 0.32, smooth=True)
    # sash / angavastra
    sash = s.get("sash")
    if sash and not female and not s.get("armor"):
        band = [(sw - 2.4, -39.4), (sw - 0.2, -37.2), (-ww + 1.0, -9.8), (-ww - 1.6, -11.6)]
        p.poly(band, fill=sash)
        p.line([(sw - 2.0, -39.0), (-ww - 1.2, -11.2)], shade(sash, -0.3), 0.18)
        # loose end fluttering at the hip
        p.poly([(-ww - 1.6, -11.6), (-ww - 4.4, -6.0), (-ww - 3.0, -4.6), (-ww + 1.0, -9.8)], fill=sash, smooth=True)
    # rudraksha
    if s.get("rudraksha"):
        for k in range(17):
            a = math.radians(200 + k * (140 / 16))
            p.circle(0.3 + math.cos(a) * 5.4, -38.6 - math.sin(a) * 6.0 - 1.4, 0.48, fill="#6a2f1c")
    # crossed warrior straps (Bhima-style bandolier)
    if s.get("straps") and not female:
        sc = s.get("strap_color", "#e2bc5a")
        for (x0, y0, x1, y1) in ((sw - 2.0, -38.6, -ww + 0.4, -10.4), (-sw + 2.0, -38.6, ww - 0.4, -10.4)):
            p.poly(limb((x0, y0), (x1, y1), 1.5, 1.5), fill=sc)
            p.line([(x0, y0), (x1, y1)], shade(sc, -0.35), 0.12)
        p.circle(0.3, -25.0, 1.0, fill=sc, outline=shade(sc, -0.4), w=0.15)
    # necklaces: thin multi-strand gold with drop pendants (+ pearls / red beads)
    if s.get("necklace"):
        p.line(arc_pts(0.3, -39.6, 4.4, 3.4, 15, 165, 18), metal, 0.42)
        p.line(arc_pts(0.3, -39.6, 5.4, 6.2, 18, 162, 20), metal, 0.3)
        for k in range(7):
            a = math.radians(35 + k * 18.3)
            x, y = 0.3 + math.cos(a) * 5.4, -39.6 + math.sin(a) * 6.2
            p.poly([(x - 0.35, y), (x, y + 1.1), (x + 0.35, y)], fill=metal)
        p.poly([(-0.7, -34.0), (0.3, -31.2), (1.3, -34.0)], fill=metal)
        p.circle(0.3, -32.8, 0.55, fill="vermilion")
        if s.get("pearls") or female:
            for k in range(15):
                a = math.radians(20 + k * 10)
                p.circle(0.3 + math.cos(a) * 6.6, -39.0 + math.sin(a) * 9.2, 0.32, fill="#f6efdf")
        elif s.get("beads", True):
            for k in range(12):
                a = math.radians(28 + k * 11.3)
                p.circle(0.3 + math.cos(a) * 3.6, -39.6 + math.sin(a) * 2.8 + 0.6, 0.3, fill="#c4362a" if k % 2 else "#e2bc5a")
    if s.get("mundamala"):
        for k in range(13):
            a = math.radians(15 + k * 12)
            x, y = 0.3 + math.cos(a) * 7.6, -39.0 + math.sin(a) * 22.0
            p.circle(x, y, 1.0, fill="#efe6d0")
            p.circle(x - 0.35, y - 0.1, 0.22, fill=INK)
            p.circle(x + 0.35, y - 0.1, 0.22, fill=INK)
    if s.get("snake"):
        body = catmull([(sw - 1.4, -36.4), (3.0, -33.6), (-0.6, -34.0), (-4.2, -35.2), (-sw + 0.6, -38.0),
                        (-sw - 1.6, -42.6), (-sw - 0.2, -46.0)], False, 8)
        for i in range(len(body) - 1):
            p.poly(limb(body[i], body[i + 1], 1.3, 1.3), fill="#3f7a48")
        hx, hy = body[-1]
        p.poly([(hx - 1.6, hy + 1.0), (hx - 1.4, hy - 1.4), (hx + 0.2, hy - 2.4), (hx + 1.8, hy - 1.4), (hx + 1.6, hy + 1.0)],
               fill="#3f7a48", smooth=True)
        p.pattern(body, "speckle", "#9fd08a", 1.2, 0.3)
        p.circle(hx + 0.6, hy - 1.0, 0.25, fill="#f2d36a")
    # waist band (kamarbandh): gold belt, bead row, little tassels
    x0, x1 = -b["hw"] - 0.2 - b["belly"] * 0.1, b["hw"] + 0.2 + b["belly"] * 0.3
    p.poly([(x0, -4.8), (x1, -4.8), (b["hw"] - 0.1, -1.0), (-b["hw"] + 0.1, -1.0)], fill=metal)
    p.line([(x0 + 0.3, -3.9), (x1 - 0.3, -3.9)], shade(metal, -0.4), 0.14)
    for k in range(9):
        xx = -b["hw"] + 0.9 + k * (2 * b["hw"] - 1.8) / 8
        p.circle(xx, -2.6, 0.32, fill="vermilion" if k % 2 else "emerald")
        if k % 2 == 0:
            p.poly([(xx - 0.3, -1.1), (xx, 0.6), (xx + 0.3, -1.1)], fill=metal)
    return fin(p, seed=1)


def build_waist(s, b, ppu):
    """Long narrow striped front flap (patka) with a tassel, hanging over the dhoti between the legs."""
    p = Pen((-6, -3, 6, 24), ppu)
    col, pat, pc = (s["dhoti"] + [None, None])[:3]
    metal = s["metal"]
    stripes = [metal, "vermilion" if col not in ("vermilion", "#c63f28") else "#2f6a3a", metal]
    w = 3.0
    flap = [(-w / 2, -1.6), (w / 2, -1.6), (w / 2 + 0.3, 17.0), (0, 19.2), (-w / 2 - 0.3, 17.0)]
    p.poly(flap, fill=stripes[0])
    for k, c in enumerate(stripes):
        x0 = -w / 2 + k * w / 3
        p.poly([(x0 + 0.1, -1.2), (x0 + w / 3 - 0.1, -1.2), (x0 + w / 3 - 0.05 + (k - 1) * 0.1, 16.6), (x0 + 0.05 + (k - 1) * 0.1, 16.6)],
               fill=c)
    p.line([(-w / 2 - 0.3, 17.0), (0, 19.2), (w / 2 + 0.3, 17.0)], shade(metal, -0.35), 0.2)
    p.line([(0, 19.2), (0, 21.0)], metal, 0.3)
    p.poly([(-0.7, 21.0), (0, 23.2), (0.7, 21.0)], fill="vermilion")
    return fin(p, seed=2, inner=0.25, ow=0.45)


# =========================================================================== arms & hands

def _hand(p, y, skin, mode="grip", metal="gold", female=False):
    if mode == "grip":
        p.poly([(-1.7, y - 0.4), (1.7, y - 0.4), (2.0, y + 2.2), (1.2, y + 3.4), (-1.3, y + 3.4), (-1.9, y + 2.0)],
               fill=skin, smooth=True)
        for k in range(3):
            p.line([(-1.2, y + 1.3 + k * 0.7), (1.4, y + 1.3 + k * 0.7)], shade(skin, -0.4), 0.13)
        p.line([(1.6, y + 0.4), (0.4, y + 1.0)], shade(skin, -0.4), 0.16)
    else:  # open palm — abhaya / varada mudra
        p.poly([(-1.6, y - 0.4), (1.6, y - 0.4), (1.8, y + 2.6), (-1.6, y + 2.6)], fill=skin, smooth=True)
        for k, (dx, L) in enumerate(((-1.15, 3.2), (-0.38, 3.9), (0.38, 3.7), (1.12, 3.0))):
            p.poly(limb((dx, y + 2.2), (dx * 1.05, y + 2.2 + L), 0.78, 0.66), fill=skin)
        p.poly(limb((1.6, y + 0.6), (2.9, y + 2.4), 0.8, 0.7), fill=skin)
        p.circle(0.0, y + 1.4, 0.42, fill="vermilion" if female else shade(skin, -0.2))
        for k in range(2):
            p.line([(-1.2, y + 2.3 + k * 0.1), (1.2, y + 2.2)], shade(skin, -0.35), 0.1)


def build_upper_arm(s, b, ppu, armor=None):
    w0, w1 = b["ua"]
    L = 14.6 * b.get("arm_k", 1.0)
    p = Pen((-5, -4.5, 5, L + 3), ppu)
    skin = s["skin"]
    p.circle(0, 0.2, w0 * 0.62, fill=skin)                   # round shoulder cap (cut-out joint piece)
    p.poly(limb((0, 0), (0, L), w0 * 0.98, w1), fill=skin)
    p.line(arc_pts(0, 0.2, w0 * 0.62, w0 * 0.62, 200, 340, 10), body_line(skin), 0.16)
    if armor:
        p.poly([(-w0 * 0.66, -1.6), (w0 * 0.66, -1.6), (w0 * 0.58, 3.6), (0, 4.8), (-w0 * 0.58, 3.6)], fill=armor,
               smooth=True)
        p.pattern([(-w0 * 0.62, -1.2), (w0 * 0.62, -1.2), (w0 * 0.55, 3.6), (-w0 * 0.55, 3.6)], "scales",
                  shade(armor, -0.35), 1.2, 0.4)
    if s.get("female") and s.get("choli"):
        p.poly([(-w0 * 0.6, -1.2), (w0 * 0.6, -1.2), (w0 * 0.52, 3.2), (-w0 * 0.52, 3.2)], fill=s["choli"])
        p.line([(-w0 * 0.52, 3.2), (w0 * 0.52, 3.2)], s["metal"], 0.35)
    y = 6.0                                                    # bajuband: double band + leaf ornament
    for dy in (0, 1.1):
        p.poly(limb((-w0 * 0.52, y + dy), (w0 * 0.5, y + dy), 0.7, 0.7), fill=s["metal"])
    p.poly([(-0.9, y - 0.3), (0, y - 2.4), (0.9, y - 0.3)], fill=s["metal"])
    p.circle(0, y - 0.9, 0.34, fill="vermilion")
    p.rivet(0, 0.2, 0.78)
    return fin(p, seed=3)


def build_forearm(s, b, ppu, mode="grip"):
    w0, w1 = b["fa"]
    L = 12.6 * b.get("arm_k", 1.0)
    p = Pen((-4.4, -3, 4.4, L + 2), ppu)
    skin = s["skin"]
    p.circle(0, 0, w0 * 0.52, fill=skin)
    p.poly(limb((0, 0), (0, L), w0, w1 * 1.05), fill=skin)
    for k in range(3 if s.get("female") else 2):
        p.poly(limb((-w1 * 0.6, L - 2.0 + k * 0.62), (w1 * 0.6, L - 2.0 + k * 0.62), 0.46, 0.46),
               fill=s["metal"] if k % 2 == 0 else ("vermilion" if s.get("female") else shade(s["metal"], -0.2)))
    p.rivet(0, 0, 0.64)
    return fin(p, seed=4)


def build_hand(s, ppu, mode="grip"):
    """Hand as its own cut-out piece pinned at the wrist (rivet) — reference puppets bend at the wrist."""
    p = Pen((-3.6, -1.6, 3.8, 9.4), ppu)
    skin = s["skin"]
    _hand(p, 0.2, skin, mode, s["metal"], s.get("female", False))
    p.rivet(0, 0.1, 0.5)
    return fin(p, seed=14, ow=0.5)


# =========================================================================== lower body

def _leg_cloth(s, back):
    col, pat, pc = (s["dhoti"] + [None, None])[:3]
    lower = s["lower"]
    if lower == "tiger":
        col, pat, pc = "#e0a040", "tiger", INK
    elif lower == "valkal":
        col, pat, pc = "#9a6a3a", "vstripes", "#6a4422"
    elif lower == "loin":
        pat, pc = None, None
    elif lower == "armor":
        col = s.get("armor") or "#9a9488"
        pat, pc = "scales", shade(col, -0.35)
    if back:
        col = shade(col, -0.1)
    return col, pat, pc


def knee_of(s):
    return 21.5 if s["lower"] != "loin" else 9.0


def build_thigh(s, b, ppu, back=False):
    """Hip -> knee: the puffy dhoti piece with its striped hem (overlaps the shin like a real cut-out)."""
    lw = b["lw"]
    knee = knee_of(s)
    p = Pen((-9, -3, 9, knee + 4), ppu)
    skin = s["skin"] if not back else shade(s["skin"], -0.08)
    col, pat, pc = _leg_cloth(s, back)
    if s["lower"] == "loin":
        p.poly(limb((0, 0), (0.2, knee + 1), lw * 1.0, lw * 0.85), fill=skin)
    cloth = [(-lw * 0.86, -1.6), (lw * 0.9, -1.6), (lw * 1.06, 6.0), (lw * 1.08, knee - 2.0), (lw * 0.85, knee + 1.2),
             (-lw * 0.9, knee + 1.2), (-lw * 1.02, knee - 2.4), (-lw * 0.98, 6.0)]
    if s["lower"] == "loin":
        cloth = [(-lw * 0.9, -1.6), (lw * 0.95, -1.6), (lw * 1.0, 4.0), (-lw * 0.95, 4.4)]
    p.poly(cloth, fill=col, smooth=s["lower"] != "loin", n=6)
    if pat:
        p.pattern(cloth, pat, pc, 1.5 if pat == "dots" else 1.9, 0.42 if pat == "dots" else 0.5, smooth=True)
    if s["lower"] != "loin":
        for k in range(3):
            x = -lw * 0.5 + k * lw * 0.5
            p.line([(x, 2.0), (x + 0.6, knee - 3.0)], shade(col, -0.28), 0.16)
        hem = [(-lw * 0.92, knee - 1.4), (lw * 0.9, knee - 1.4), (lw * 0.86, knee + 1.2), (-lw * 0.92, knee + 1.2)]
        p.poly(hem, fill=s["metal"])
        p.pattern(hem, "dots", "vermilion", 1.0, 0.3)
    p.rivet(0.0, 0.6, 0.6)
    return fin(p, seed=5 + back)


def build_shin(s, b, ppu, back=False):
    """Knee -> foot (pivot at the knee rivet): calf, anklet with bells, foot."""
    lw = b["lw"]
    knee = knee_of(s)
    L = 47.6 - knee
    p = Pen((-6, -3, 8, L + 1.5), ppu)
    skin = s["skin"] if not back else shade(s["skin"], -0.08)
    p.circle(0.1, 0.0, lw * 0.44, fill=skin)
    p.poly(limb((0.1, 0.0), (0.6, L - 4.2), lw * 0.84, lw * 0.56), fill=skin)
    p.poly([(-lw * 0.42, 2.0), (-lw * 0.64, 7.0), (-lw * 0.3, 12.0)], fill=skin, smooth=True)
    y = L - 5.8
    p.poly(limb((-lw * 0.33, y), (lw * 0.38, y), 0.9, 0.9), fill=s["metal"])
    for k in range(4):
        p.circle(-lw * 0.28 + k * lw * 0.22, y + 1.1, 0.3, fill=s["metal"])
    foot = [(-1.9, L - 4.6), (1.4, L - 4.2), (4.4, L - 2.6), (5.9, L - 0.9), (5.4, L), (-1.7, L), (-2.4, L - 2.0)]
    p.poly(foot, fill=skin, smooth=True)
    if s.get("female"):
        p.line([(-1.9, L - 0.4), (5.4, L - 0.4)], "#c4362a", 0.4)
    p.line([(3.4, L - 1.0), (4.4, L - 0.4)], shade(skin, -0.4), 0.12)
    p.rivet(0.1, 0.0, 0.62)
    return fin(p, seed=7 + back)


SEAT_DROP = {"stone": 5.6, "cushion": 2.4, "none": 0.0}


def _seat(p, s, w, y):
    """Red cushion (gold stripe) + dark stone pedestal under seated puppets (reference)."""
    seat = s.get("seat", "stone")
    if seat == "none":
        return
    cc = s.get("cushion_color", "#b8452c")
    if seat == "stone":
        p.poly([(-w - 1.6, y + 2.0), (w + 1.6, y + 2.0), (w + 1.2, y + 5.6), (-w - 1.2, y + 5.6)], fill="#3a302c")
        p.line([(-w - 1.4, y + 2.6), (w + 1.4, y + 2.6)], "#5a4e46", 0.3)
        p.pattern([(-w - 1.6, y + 2.0), (w + 1.6, y + 2.0), (w + 1.2, y + 5.6), (-w - 1.2, y + 5.6)], "speckle", "#4e4440",
                  1.4, 0.3)
    p.poly([(-w - 0.8, y - 0.6), (w + 0.8, y - 0.6), (w + 1.4, y + 1.0), (w + 0.6, y + 2.4), (-w - 0.6, y + 2.4),
            (-w - 1.4, y + 1.0)], fill=cc, smooth=True)
    p.line([(-w - 0.8, y + 0.9), (w + 0.8, y + 0.9)], "#e2bc5a", 0.45)
    p.pattern([(-w, y - 0.4), (w, y - 0.4), (w, y + 2.2), (-w, y + 2.2)], "dots", shade(cc, 0.35), 1.4, 0.3)


def build_lap(s, b, ppu):
    """Seated lower body: crossed legs (men) or legs folded to one side under the saree (women)."""
    p = Pen((-17, -4, 17, 18), ppu)
    female = s.get("female") or s["lower"] == "saree"
    col, pat, pc = (s["dhoti"] + [None, None])[:3]
    if female:
        sr = s["saree"]
        col, pat, pc = sr[0], sr[1], shade(sr[0], 0.45)
    if s["lower"] == "tiger":
        col, pat, pc = "#e0a040", "tiger", INK
    if s["lower"] == "valkal":
        col, pat, pc = "#9a6a3a", "vstripes", "#6a4422"
    skin = s["skin"]
    w = 12.0 + b["belly"] * 0.4
    _seat(p, s, w, 9.4)
    if female:
        lap = [(-w + 1.0, 0.4), (-w - 0.6, 5.0), (-w + 0.4, 9.6), (w + 1.6, 9.6), (w + 2.6, 7.4), (w - 1.0, 3.0),
               (5.0, -1.6), (-5.0, -1.6)]
        p.poly(lap, fill=col, smooth=True, n=8)
        if pat:
            p.pattern(lap, pat, pc, 1.6, 0.42, smooth=True)
        border = sr[2] if len(sr) > 2 else "gold"
        p.line([(-w + 0.4, 9.0), (w + 1.6, 9.0)], border, 0.7)
        for k in range(5):
            p.line([(2.0 + k * 1.6, 1.0), (3.4 + k * 2.2, 8.8)], shade(col, -0.3), 0.16)
        f = [(w - 0.6, 6.6), (w + 3.6, 6.6), (w + 4.4, 8.2), (w + 3.4, 9.4), (w - 0.2, 9.4)]
        p.poly(f, fill=skin, smooth=True)
        p.line([(w + 0.2, 9.0), (w + 3.6, 9.0)], "#c4362a", 0.4)
        p.poly(limb((w - 0.2, 7.4), (w - 0.2, 9.0), 0.9, 0.9), fill=s["metal"])
        return fin(p, seed=6)
    lap = [(-w, 1.2), (-w - 1.2, 5.6), (-w + 1.4, 9.4), (w - 1.0, 9.4), (w + 1.4, 5.8), (w, 1.0), (5.0, -1.6),
           (-5.0, -1.6)]
    p.poly(lap, fill=col, smooth=True, n=8)
    if pat:
        p.pattern(lap, pat, pc, 1.6, 0.42, smooth=True)
    p.line([(-w + 1.0, 6.8), (-2.0, 4.4), (2.0, 4.4), (w - 0.6, 6.8)], shade(col, -0.3), 0.2, smooth=True)
    for sx in (-1, 1):
        f = [(sx * 2.0, 2.6), (sx * 6.6, 1.2), (sx * 8.4, 2.4), (sx * 6.8, 4.0), (sx * 2.4, 4.4)]
        p.poly(f, fill=skin, smooth=True)
        p.line([(sx * 6.4, 1.6), (sx * 7.8, 2.6)], "#c4362a", 0.3)
        p.poly(limb((sx * 8.2, 3.2), (sx * 9.2, 4.6), 1.0, 1.0), fill=s["metal"])
    p.line([(-w + 0.2, 8.6), (w - 0.2, 8.6)], s["metal"], 0.5)
    p.rivet(-w + 2.4, 6.4, 0.55)
    p.rivet(w - 2.0, 6.4, 0.55)
    return fin(p, seed=6)


def build_skirt(s, b, ppu):
    """Saree skirt for standing female puppets (legs hidden)."""
    p = Pen((-14, -6, 15, 50), ppu)
    sr = s["saree"]
    col, pat, border = sr[0], sr[1], sr[2] if len(sr) > 2 else "gold"
    sk = [(-b["hw"] - 0.2, -3.6), (b["hw"] + 0.2, -3.6), (b["hw"] + 1.6, 10.0), (11.0, 44.2), (-9.8, 44.2),
          (-b["hw"] - 1.6, 10.0)]
    p.poly(sk, fill=col, smooth=False)
    if pat:
        p.pattern(sk, pat, shade(col, 0.45), 1.8, 0.45)
    for k in range(6):
        x0 = 1.0 + k * 0.6
        p.line([(x0, 0), (1.6 + k * 1.6, 43.0)], shade(col, -0.3), 0.18)
    hem = [(-10.0, 40.8), (11.2, 40.8), (11.2, 44.2), (-9.8, 44.2)]
    p.poly(hem, fill=border)
    p.pattern(hem, "zigzag", shade(col, -0.1), 1.2, 0.3)
    skin = s["skin"]
    foot = [(1.6, 43.8), (5.0, 44.4), (7.6, 46.4), (7.2, 47.6), (1.2, 47.6)]
    p.poly(foot, fill=skin, smooth=True)
    p.line([(1.2, 47.2), (7.2, 47.2)], "#c4362a", 0.4)
    p.poly(limb((1.6, 44.4), (4.0, 44.4), 0.7, 0.7), fill=s["metal"])
    return fin(p, seed=7)


def build_serpent_tail(s, b, ppu):
    p = Pen((-22, -6, 22, 50), ppu)
    c = s.get("tail_color", "#3f7a48")
    path = catmull([(0, -2), (3.0, 10.0), (-2.0, 22.0), (2.0, 34.0), (12.0, 42.0), (16.0, 38.0), (8.0, 36.0),
                    (-8.0, 40.0), (-16.0, 44.0), (-20.0, 40.0)], False, 8)
    n = len(path)
    for i in range(n - 1):
        w = 13.0 * (1 - i / n) + 1.4
        p.poly(limb(path[i], path[i + 1], w, w * 0.98), fill=c)
    p.pattern(path + [(0, 50)], "scales", shade(c, 0.3), 1.5, 0.4)
    for i in range(0, n - 1, 3):
        x, y = path[i]
        w = 13.0 * (1 - i / n) + 1.4
        p.line([(x - w * 0.18, y), (x + w * 0.18, y)], "#e8d8a0", 0.6)
    return fin(p, seed=8)


def build_fish_tail(s, b, ppu):
    p = Pen((-14, -6, 22, 50), ppu)
    c = s.get("tail_color", "#3f8f8a")
    body = [(-7.0, -3.6), (7.0, -3.6), (8.4, 10.0), (6.0, 26.0), (3.2, 36.0), (0.6, 36.0), (-3.6, 24.0), (-7.6, 10.0)]
    p.poly(body, fill=c, smooth=True)
    p.pattern(body, "scales", "gold", 1.6, 0.42, smooth=True)
    fin_pts = [(1.6, 34.0), (12.0, 40.0), (16.0, 47.0), (8.0, 44.0), (2.0, 48.0), (-3.0, 44.0), (0.4, 36.0)]
    p.poly(fin_pts, fill=shade(c, 0.15), smooth=True)
    for k in range(5):
        p.line([(1.4, 36.0), (4.0 + k * 2.6, 46.0 - k * 0.6)], shade(c, -0.3), 0.18)
    return fin(p, seed=9)


def build_tail(s, ppu):
    """Vanara tail built from small riveted segments, ending in a flame-like tuft (reference)."""
    p = Pen((-15, -36, 6, 5), ppu)
    c = s.get("tail_color", s["skin"])
    path = catmull([(0, 0), (-4.8, -1.4), (-9.0, -7.0), (-8.6, -15.0), (-5.0, -20.6), (-1.6, -24.4), (-1.6, -28.0),
                    (-3.6, -29.8)], False, 4)
    n = len(path)
    for i in range(n - 1):
        w = 2.5 * (1 - i / n) + 1.0
        p.poly(limb(path[i], path[i + 1], w, w * 0.94), fill=c if i % 2 == 0 else shade(c, 0.07), outline=INK, w=0.16)
        x, y = path[i]
        p.circle(x, y, 0.32, fill="#efe2c0")
    tx, ty = path[-1]
    for k, ang in enumerate((-150, -110, -70)):
        a_ = math.radians(ang)
        p.poly([(tx - 0.6, ty), (tx + math.cos(a_) * 3.2, ty + math.sin(a_) * 3.2), (tx + 0.6, ty)], fill="vermilion",
               smooth=True)
    p.circle(tx, ty, 0.7, fill="gold")
    p.rivet(0, 0, 0.6)
    return fin(p, seed=10)


def build_quiver(s, ppu):
    """Red quiver with gold bands and fletched arrows, worn on the back."""
    p = Pen((-4, -15, 4, 14), ppu)
    p.poly(limb((0, 12), (0, -6), 3.2, 2.8), fill="#a8382a")
    for y in (9.0, 2.0, -4.0):
        p.poly(limb((-1.6, y), (1.6, y), 0.7, 0.7), fill="#e2bc5a")
    for k, dx in enumerate((-0.9, 0.0, 0.9)):
        p.line([(dx, -6), (dx * 1.3, -11.5)], "#c8a060", 0.24)
        p.poly([(dx * 1.3, -11.5), (dx * 1.3 - 0.7, -13.8), (dx * 1.3 + 0.7, -13.8)], fill="#e8e0d0" if k % 2 else "vermilion")
    return fin(p, seed=15, ow=0.45)


def build_wing(s, ppu):
    p = Pen((-30, -32, 6, 14), ppu)
    c = s.get("wing_color", "#c8642a")
    c2 = s.get("wing_color2", "gold")
    pts = [(0, 0), (-6, -10), (-14, -20), (-26, -29), (-24, -22), (-28, -18), (-22, -14), (-26, -8), (-18, -6),
           (-20, 0), (-12, 0), (-12, 6), (-5, 4)]
    p.poly(pts, fill=c, smooth=False)
    for k in range(6):
        x = -6 - k * 3.4
        p.line([(x + 2, -6 - k * 2.2), (x - 4, -2 - k * 2.4)], shade(c, -0.35), 0.2)
    p.poly([(0, 0), (-6, -10), (-14, -18), (-10, -8), (-4, -3)], fill=c2, smooth=True)
    p.pattern([(0, 0), (-6, -10), (-14, -18), (-10, -8), (-4, -3)], "scales", shade(c2, -0.35), 1.2, 0.35, smooth=True)
    p.rivet(0, 0, 0.7)
    return fin(p, seed=11)


def build_halo(s, ppu):
    p = Pen((-17, -17, 17, 17), ppu)
    c = s.get("halo_color", "gold")
    for k in range(28):
        a = math.radians(k * (360 / 28))
        p.poly([(math.cos(a - 0.07) * 11.5, math.sin(a - 0.07) * 11.5), (math.cos(a) * 16.0, math.sin(a) * 16.0),
                (math.cos(a + 0.07) * 11.5, math.sin(a + 0.07) * 11.5)], fill=shade(c, -0.05))
    p.circle(0, 0, 12.0, fill=c)
    p.circle(0, 0, 10.4, fill=shade(c, 0.35))
    p.circle(0, 0, 10.4, outline=shade(c, -0.3), w=0.25)
    for k in range(24):
        a = math.radians(k * 15)
        p.circle(math.cos(a) * 11.2, math.sin(a) * 11.2, 0.35, fill="vermilion")
    return fin(p, seed=12, inner=0.15, ow=0.3, bevel=0.1, rim=0.08)


def build_head(s, ppu, scale=1.0):
    p = Pen((-17, -46, 17, 30), ppu * scale)
    draw_head(p, s)
    return fin(p, seed=13)


# =========================================================================== assembly

ITEM_POSES = {
    # how a hand holding X sits at rest: (upper, fore) angles for front & back arms
    "bow": ((-20, -55), (25, -40)), "gada": ((-12, -118), (22, -105)), "default": ((-12, -105), (22, -100)),
}


def _cache_path(spec, ppu):
    key = stable_hash({"spec": spec, "ppu": ppu, "v": BUILD_VERSION})
    return CACHE_DIR / "rigs" / f"{spec.get('id', 'char')}_{key}.pkl"


def build_character(spec: dict, ppu: float = 9.0, use_cache=True) -> Rig:
    cp = _cache_path(spec, ppu)
    if use_cache and cp.exists():
        try:
            with open(cp, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    s = resolve(spec)
    b = dict(BUILDS.get(s["build"], BUILDS["hero"]))
    female = s["female"]
    rig = Rig(spec.get("id", "char"), ppu)
    rig.meta = {"spec": s, "kind": "humanoid", "seatable": True}

    rig.add(Part("torso", build_torso(s, b, ppu), None, (0, 0), z=10))
    head_scale = 1.18 if s["build"] == "child" else 1.0
    if s["head"] == "elephant":
        head_scale *= 1.28
    hs = dict(s)
    rig.add(Part("head", build_head(hs, ppu, head_scale), "torso", (0.8, -39.4), z=30))
    # extra heads (Ravana, Brahma, Kartikeya, Panchmukhi...)
    extra = list(s.get("heads") or [])
    n = len(extra)
    for i, htype in enumerate(extra):
        es = dict(hs)
        es.update({"head": htype, "crown": s.get("extra_crown", s["crown"] if htype == "human" else "kirita_low"),
                   "plume": False})
        if htype != "human":
            es["skin"] = s.get("extra_skin", {}).get(htype, s["skin"]) if isinstance(s.get("extra_skin"), dict) else s["skin"]
        if n >= 5:     # Ravana / Vishwaroop: a fanned arc of heads around the main head
            k = 0.58
            span = 128 if n >= 8 else 100
            ang = math.radians(-span + 2 * span * i / max(1, n - 1))
            R = 17.0
            cx, cy = 0.8 + R * math.sin(ang), -46.0 - R * 0.95 * math.cos(ang)
            joint = (cx, cy + 8.0 * k)
            z = 20 - abs(i - (n - 1) / 2)
        else:          # 2-4 heads: side by side
            side = 1 if i % 2 == 0 else -1
            rank = i // 2 + 1
            k = 0.92 - 0.05 * rank
            joint = (0.8 + side * rank * 6.4, -39.0 - rank * 0.4)
            z = 24 - rank
        rig.add(Part(f"head_x{i}", build_head(es, ppu, k), "torso", joint, z=z))
    # arms
    items = s.get("items") or {}
    armor = s.get("armor")
    for side, sx, zu, zf in (("f", 1, 40, 41), ("b", -1, 4, 5)):
        it = items.get(side)
        mode = "grip" if it and it not in ("abhaya", "varada") else "open"
        rig.add(Part(f"ua_{side}", build_upper_arm(s, b, ppu, armor), "torso",
                     (sx * (b["sw"] - 1.5), -36.4), z=zu, rest=-14 * sx))
        rig.add(Part(f"fa_{side}", build_forearm(s, b, ppu, mode), f"ua_{side}", (0, 14.6), z=zf))
        rig.add(Part(f"hd_{side}", build_hand(s, ppu, mode), f"fa_{side}", (0, 12.6), z=zf + 2))
        if it and it in ITEMS:
            spr, world, off = build_item(it, ppu)
            front_items = ("dhal", "shield", "chakra", "sudarshan", "shankh", "padma", "kalash", "modak", "diya")
            rig.add(Part(f"it_{side}", spr, f"hd_{side}", (off[0], 2.0 + off[1]),
                         z=zf + 1 if it not in front_items else zf + 3, rest=ITEM_REST.get(it, 0.0), world=world))
    # rest pose for the two main arms
    rig.parts["ua_b"].rest = 22
    rig.parts["fa_b"].rest = -108 if not items.get("b") else -60
    rig.parts["ua_f"].rest = -14
    rig.parts["fa_f"].rest = -112 if items.get("f") else -100
    # extra arms (fan behind the body)
    extra = s.get("extra_items") or []
    n_extra = max(0, int(s.get("arms", 2)) - 2)
    for i in range(n_extra):
        side = "f" if i % 2 == 0 else "b"
        sx = 1 if side == "f" else -1
        rank = i // 2
        tot = max(1, n_extra // 2)
        it = extra[i] if i < len(extra) else None
        mode = "grip" if it and it in ITEMS else "open"
        ua_rest = sx * -(150 - rank * (110 / max(1, tot)))
        fa_rest = sx * -35
        name = f"x{i}"
        rig.add(Part(f"ua_{name}", build_upper_arm(s, b, ppu * 0.98, None), "torso",
                     (sx * (b["sw"] - 2.2), -35.6 + rank * 1.2), z=2 - rank, rest=ua_rest))
        rig.add(Part(f"fa_{name}", build_forearm(s, b, ppu * 0.98, mode), f"ua_{name}", (0, 14.3), z=3 - rank,
                     rest=fa_rest))
        rig.add(Part(f"hd_{name}", build_hand(s, ppu * 0.98, mode), f"fa_{name}", (0, 12.4), z=4 - rank))
        if it and it in ITEMS:
            spr, world, off = build_item(it, ppu * 0.98)
            rig.add(Part(f"it_{name}", spr, f"hd_{name}", (0, 2.0), z=3 - rank, world=world,
                         rest=ITEM_REST.get(it, 0.0)))
    # lower body
    lower = s["lower"]
    if lower in ("saree",) or (female and lower not in ("serpent", "fish", "dhoti", "tiger", "valkal")):
        rig.add(Part("skirt", build_skirt(s, b, ppu), "torso", (0, 0), z=12))
        rig.ground = 47.6
        rig.meta["legs"] = False
    elif lower == "serpent":
        rig.add(Part("tail_lower", build_serpent_tail(s, b, ppu), "torso", (0, 0), z=8))
        rig.ground = 46.0
        rig.meta["legs"] = False
        rig.meta["seatable"] = False
    elif lower == "fish":
        rig.add(Part("tail_lower", build_fish_tail(s, b, ppu), "torso", (0, 0), z=8))
        rig.ground = 47.0
        rig.meta["legs"] = False
        rig.meta["seatable"] = False
    else:
        kn = knee_of(s)
        rig.add(Part("leg_b", build_thigh(s, b, ppu, back=True), "torso", (-2.6, 0.2), z=6, rest=3))
        rig.add(Part("shin_b", build_shin(s, b, ppu, back=True), "leg_b", (0.3, kn + 0.4), z=5))
        rig.add(Part("leg_f", build_thigh(s, b, ppu), "torso", (2.8, 0.2), z=14, rest=-3))
        rig.add(Part("shin_f", build_shin(s, b, ppu), "leg_f", (0.3, kn + 0.4), z=13))
        rig.add(Part("waist", build_waist(s, b, ppu), "torso", (0.2, -2.2), z=16))
        rig.ground = 47.4
        rig.meta["legs"] = True
    if rig.meta.get("seatable"):
        lap = Part("lap", build_lap(s, b, ppu), "torso", (0, 0), z=15)
        lap.visible = False
        rig.add(lap)
    if s.get("tail"):
        rig.add(Part("tail", build_tail(s, ppu), "torso", (-b["hw"] + 1.0, -3.0), z=3))
    if s.get("wings"):
        rig.add(Part("wing_b", build_wing(s, ppu), "torso", (-b["sw"] + 3.0, -35.0), z=0, rest=8))
        wf = build_wing(dict(s, wing_color=shade(s.get("wing_color", "#c8642a"), -0.12)), ppu)
        rig.add(Part("wing_f", wf, "torso", (b["sw"] - 4.0, -35.6), z=1, rest=-4))
    if s.get("halo"):
        rig.add(Part("halo", build_halo(s, ppu), "torso", (0.6, -48.0), z=-10, world=0.0))
    # string anchors (head top, both hands)
    if "bow" in (items.get("f"), items.get("b")) or s.get("quiver"):
        rig.add(Part("quiver", build_quiver(s, ppu), "torso", (-b["sw"] + 3.4, -28.0), z=3, rest=28))
    rig.meta["ground_seated"] = 9.4 + SEAT_DROP.get(s.get("seat", "stone"), 5.6)
    rig.anchors = {"head": ("head", (-0.3, -26.0 if s["crown"] in ("kirita", "kirita_tall") else -16.0)),
                   "hand_f": ("hd_f", (0, 1.6)), "hand_b": ("hd_b", (0, 1.6))}
    sc = b["s"] * float(s.get("scale", 1.0))
    rig.meta["scale"] = sc
    rig.extent = (-48, -84, 48, 56)
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        with open(cp, "wb") as f:
            pickle.dump(rig, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return rig
