"""Puppet action library.

A performer's state at time t = rest pose + persistent effects of every action
that has started (walk moves x, sit switches to the lap, fall leaves the body
lying, vanish leaves alpha 0 ...) + the always-on puppet idle (string sway).

Actions in a storyboard:   {do: walk, at: 1.5, dur: 2.0, to: 0.7}
Every action accepts: at (s, shot-relative), dur (s), and its own params.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .util import clamp, ease_in_out, ease_out, ease_back, lerp, smooth


@dataclass
class State:
    x: float                 # stage x (0..1 of frame width)
    face: int = 1            # +1 right, -1 left
    mode: str = "stand"      # stand | seated | fly | lying
    dy: float = 0.0          # vertical offset in rig units (negative = up)
    dx: float = 0.0          # horizontal offset in rig units (sway)
    rot: float = 0.0         # root rotation (deg)
    alpha: float = 1.0
    scale: float = 1.0
    flipx: float = 1.0       # for turn squash (cos curve)
    glow: float = 0.0        # extra divine glow 0..1
    pose: dict = field(default_factory=dict)
    talking: float = 0.0
    walking: bool = False
    flying: bool = False
    hidden: set = field(default_factory=set)
    show: set = field(default_factory=set)
    shake: float = 0.0
    silhouette: bool = False

    def add(self, part, ang):
        self.pose[part] = self.pose.get(part, 0.0) + ang

    def set(self, part, ang, w=1.0):
        """Blend toward an absolute pose angle (delta from rest) by weight w."""
        self.pose[part] = lerp(self.pose.get(part, 0.0), ang, w)


def _env(lt, dur, ramp=0.3):
    """Hold-envelope: ramps in & out over `ramp` seconds."""
    if lt < 0 or lt > dur + ramp:
        return 0.0
    r = min(ramp, dur / 2 + 1e-6)
    if lt < r:
        return smooth(lt / r)
    if lt > dur - r:
        return smooth((dur + 0.0 - lt) / r) if lt <= dur else 0.0
    return 1.0


def _noise1(t, seed=0.0):
    return (math.sin(t * 1.7 + seed) * 0.5 + math.sin(t * 2.9 + seed * 2.1) * 0.3 + math.sin(t * 5.3 + seed * 0.7) * 0.2)


# ============================================================ humanoid actions
# rest pose (rig): ua_f -14, fa_f -112/-100 (forearm raised forward), ua_b +22, fa_b -108 (hand on hip)

def a_walk(st, lt, a, rig, ctx):
    dur = a.get("dur", 2.0)
    x0 = a.get("_from", st.x)
    x1 = a.get("to", x0 + 0.25 * st.face)
    k = ease_in_out(lt / dur) if a.get("ease", True) else clamp(lt / dur)
    st.x = lerp(x0, x1, k)
    if a.get("face", "auto") == "auto" and abs(x1 - x0) > 1e-3:
        st.face = 1 if x1 > x0 else -1
    if lt <= dur:
        st.walking = True
        steps = a.get("steps", max(2.0, abs(x1 - x0) * 9.0))
        ph = (lt / dur) * steps * math.pi
        w = _env(lt, dur, 0.25)
        run = a.get("run", False)
        amp = 24 if run else 17
        kind = rig.meta.get("kind")
        if kind == "humanoid":
            if rig.meta.get("legs", True):
                st.add("leg_f", -amp * math.sin(ph) * w)
                st.add("leg_b", amp * math.sin(ph) * w)
            st.add("ua_f", 8 * math.sin(ph) * w)
            st.add("ua_b", -10 * math.sin(ph) * w)
            st.dy -= abs(math.sin(ph)) * (2.6 if run else 1.6) * w   # the puppet hop
            st.rot += (3.5 if run else 2.0) * math.sin(2 * ph) * w + (4 if run else 1.5) * w
        elif kind == "quadruped":
            amp = 30 if run else 20
            s = math.sin(ph)
            st.add("leg_fn", -amp * s * w)
            st.add("leg_hf", -amp * s * w)
            st.add("leg_ff", amp * s * w)
            st.add("leg_hn", amp * s * w)
            st.add("head", 4 * math.sin(2 * ph) * w)
            st.add("tail", 10 * math.sin(ph) * w)
            st.dy -= abs(math.sin(ph)) * (2.0 if run else 0.8) * w
            if run:
                st.rot += 4 * math.sin(2 * ph) * w
        elif kind == "bird":
            st.dy -= abs(math.sin(ph * 2)) * 1.2 * w
            st.add("body", 3 * math.sin(ph * 2) * w)


def a_run(st, lt, a, rig, ctx):
    a2 = dict(a)
    a2["run"] = True
    a2.setdefault("dur", 1.2)
    a_walk(st, lt, a2, rig, ctx)


def a_talk(st, lt, a, rig, ctx):
    dur = a.get("dur", 2.0)
    w = _env(lt, dur, 0.2)
    if w <= 0:
        return
    st.talking = w
    sd = a.get("_seed", 1.3)
    st.add("head", (2.6 * _noise1(lt * 3.2, sd) - 1.2) * w)
    if a.get("gesture", True) and rig.meta.get("kind") == "humanoid":
        g = _noise1(lt * 0.9, sd + 4)
        st.add("fa_f", (-14 * max(0, g) - 4) * w)
        st.add("ua_f", (-10 * max(0, g)) * w)
    if rig.meta.get("kind") == "bird":
        st.add("body", 3 * math.sin(lt * 9) * w)


def _hold(st, lt, a, targets, ramp=0.35, keep=False):
    dur = a.get("dur", 2.0)
    w = smooth(lt / ramp) if lt < ramp else (1.0 if (lt <= dur or keep) else smooth(1 - (lt - dur) / ramp))
    for part, ang in targets.items():
        st.set(part, ang, w)
    return w


def a_point(st, lt, a, rig, ctx):
    _hold(st, lt, a, {"ua_f": -64, "fa_f": 90}, keep=a.get("keep", False))


def a_bless(st, lt, a, rig, ctx):
    # abhaya mudra: forearm vertical, palm out
    w = _hold(st, lt, a, {"ua_f": 4, "fa_f": -38}, keep=a.get("keep", False))
    st.glow = max(st.glow, 0.35 * w)


def a_namaste(st, lt, a, rig, ctx):
    w = _hold(st, lt, a, {"ua_f": 10, "fa_f": -45, "ua_b": -30, "fa_b": 10, "head": 6}, keep=a.get("keep", False))
    st.rot += 3 * w


def a_bow(st, lt, a, rig, ctx):
    w = _hold(st, lt, a, {"ua_f": 10, "fa_f": -45, "head": 10}, keep=a.get("keep", False))
    st.rot += 16 * w


def a_raise(st, lt, a, rig, ctx):
    _hold(st, lt, a, {"ua_f": -150, "fa_f": 90}, keep=a.get("keep", False))


def a_raise_both(st, lt, a, rig, ctx):
    w = _hold(st, lt, a, {"ua_f": -150, "fa_f": 95, "ua_b": 120, "fa_b": 100}, keep=a.get("keep", False))
    st.glow = max(st.glow, 0.25 * w)


def a_strike(st, lt, a, rig, ctx):
    """Wind-up then fast downward blow (mace / sword)."""
    dur = a.get("dur", 0.9)
    if lt < 0 or lt > dur + 0.4:
        return
    if lt < dur * 0.45:
        k = ease_out(lt / (dur * 0.45))
        st.set("ua_f", -150 * k + 0, 1)
        st.set("fa_f", 90 * k, 1)
        st.rot -= 4 * k
    elif lt < dur * 0.62:
        k = ease_out((lt - dur * 0.45) / (dur * 0.17))
        st.set("ua_f", lerp(-150, -40, k), 1)
        st.set("fa_f", lerp(90, 60, k), 1)
        st.rot += 8 * k
        st.shake = max(st.shake, 0.6 * k)
    else:
        k = smooth((lt - dur * 0.62) / (dur * 0.38 + 0.4))
        st.set("ua_f", lerp(-40, 0, k), 1)
        st.set("fa_f", lerp(60, 0, k), 1)
        st.rot += 8 * (1 - k)


def a_shoot(st, lt, a, rig, ctx):
    """Archer: bow arm forward, string arm draws back, release."""
    dur = a.get("dur", 1.6)
    if lt < 0 or lt > dur + 0.5:
        return
    w = _env(lt, dur, 0.35)
    draw = smooth(clamp((lt - 0.2) / (dur * 0.55)))
    rel = lt > dur * 0.8
    st.set("ua_f", -62, w)
    st.set("fa_f", 104, w)
    st.set("ua_b", -110 + (12 if rel else 0), w)
    st.set("fa_b", lerp(150, 270, draw) if not rel else 120, w)
    st.rot += -2 * w


def a_throw(st, lt, a, rig, ctx):
    dur = a.get("dur", 0.8)
    if lt < 0 or lt > dur + 0.4:
        return
    if lt < dur * 0.5:
        k = ease_out(lt / (dur * 0.5))
        st.set("ua_f", -170 * k, 1)
        st.set("fa_f", 100 * k, 1)
        st.rot -= 6 * k
    else:
        k = ease_out(clamp((lt - dur * 0.5) / (dur * 0.5)))
        st.set("ua_f", lerp(-170, -70, k), 1)
        st.set("fa_f", lerp(100, 100, k), 1)
        st.rot += 6 * k


def a_fight(st, lt, a, rig, ctx):
    dur = a.get("dur", 3.0)
    if lt < 0 or lt > dur:
        return
    period = a.get("period", 0.9)
    k = lt % period
    a_strike(st, k, {"dur": period * 0.85}, rig, ctx)
    st.dx += 1.2 * math.sin(lt * 3.1)


def a_sit(st, lt, a, rig, ctx):
    if lt >= 0:
        st.mode = "seated"


def a_stand(st, lt, a, rig, ctx):
    if lt >= 0:
        st.mode = "stand"
        dur = a.get("dur", 0.5)
        if lt < dur:
            st.dy += 6 * (1 - smooth(lt / dur))


def a_meditate(st, lt, a, rig, ctx):
    st.mode = "seated"
    st.set("ua_f", 18, 1)
    st.set("fa_f", -20, 1)
    st.set("ua_b", -20, 1)
    st.set("fa_b", 40, 1)
    st.glow = max(st.glow, 0.3 + 0.15 * math.sin(lt * 1.3))


def a_fly(st, lt, a, rig, ctx):
    dur = a.get("dur", 3.0)
    x0 = a.get("_from", st.x)
    x1 = a.get("to", x0 + 0.6 * st.face)
    k = ease_in_out(lt / dur)
    st.x = lerp(x0, x1, k)
    if abs(x1 - x0) > 1e-3:
        st.face = 1 if x1 > x0 else -1
    lift = a.get("height", 18.0)
    arc = math.sin(math.pi * clamp(lt / dur)) if a.get("arc", True) else (1.0 if lt > 0 else 0)
    kind = rig.meta.get("kind")
    if lt <= dur:
        st.flying = True
        if kind == "humanoid":
            w = smooth(lt / 0.4) * (1 if lt < dur - 0.3 else smooth((dur - lt) / 0.3))
            st.rot += 72 * w
            st.set("ua_f", -170, w)
            st.set("fa_f", 0, w)
            st.set("ua_b", 30, w)
            st.set("leg_f", 18, w)
            st.set("leg_b", 30, w)
            st.dy -= lift * arc + 2 * math.sin(lt * 4)
        elif kind == "bird":
            fl = math.sin(lt * a.get("flap", 11.0))
            st.set("wing_f", -45 + 70 * fl, 1)
            st.set("wing_b", -35 + 60 * math.sin(lt * a.get("flap", 11.0) - 0.4), 1)
            st.dy -= lift * arc + 1.5 * fl
            st.flying = True
        else:
            st.dy -= lift * arc


def a_hover(st, lt, a, rig, ctx):
    """Birds / divine beings floating in place (wings flapping)."""
    dur = a.get("dur", 99)
    if lt < 0 or lt > dur:
        return
    if rig.meta.get("kind") == "bird":
        fl = math.sin(lt * a.get("flap", 10.0))
        st.set("wing_f", -45 + 70 * fl, 1)
        st.set("wing_b", -35 + 60 * math.sin(lt * a.get("flap", 10.0) - 0.4), 1)
        st.flying = True
        st.dy -= a.get("height", 0) + 1.4 * fl
    else:
        st.dy -= a.get("height", 6.0) + 1.5 * math.sin(lt * 1.6)
        st.glow = max(st.glow, 0.25)


def a_jump(st, lt, a, rig, ctx):
    dur = a.get("dur", 0.9)
    if 0 <= lt <= dur:
        k = lt / dur
        st.dy -= a.get("height", 14.0) * 4 * k * (1 - k)
        if "to" in a:
            st.x = lerp(a.get("_from", st.x), a["to"], ease_in_out(k))
        st.add("leg_f", -20 * math.sin(math.pi * k))
        st.add("leg_b", 20 * math.sin(math.pi * k))
    elif lt > dur and "to" in a:
        st.x = a["to"]


def a_fall(st, lt, a, rig, ctx):
    """Collapse and stay lying (wounded / dead / fainted)."""
    dur = a.get("dur", 0.8)
    if lt < 0:
        return
    k = ease_out(clamp(lt / dur))
    st.rot += -86 * k * (-1 if a.get("back") else 1)
    st.dy += k * (rig.ground - 6.0)
    if k >= 1:
        st.mode = "lying"


def a_shake(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.0)
    if 0 <= lt <= dur:
        st.shake = max(st.shake, a.get("amount", 1.0) * _env(lt, dur, 0.1))


def a_angry(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.6)
    if 0 <= lt <= dur:
        w = _env(lt, dur, 0.2)
        st.shake = max(st.shake, 0.5 * w)
        st.set("ua_f", -40, w)
        st.set("fa_f", 60, w)
        st.add("head", -5 * w)


def a_dance(st, lt, a, rig, ctx):
    dur = a.get("dur", 4.0)
    if 0 <= lt <= dur:
        w = _env(lt, dur, 0.4)
        b = a.get("bpm", 96) / 60.0 * math.pi
        st.rot += 6 * math.sin(lt * b) * w
        st.dy -= abs(math.sin(lt * b)) * 1.6 * w
        st.add("ua_f", (-60 - 40 * math.sin(lt * b)) * w)
        st.add("ua_b", (60 + 40 * math.sin(lt * b + 1)) * w)
        st.add("head", 5 * math.sin(lt * b + 0.5) * w)


def a_laugh(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.5)
    if 0 <= lt <= dur:
        w = _env(lt, dur, 0.2)
        st.add("head", (-8 + 3 * math.sin(lt * 18)) * w)
        st.rot += 2 * math.sin(lt * 18) * w


def a_sad(st, lt, a, rig, ctx):
    w = _hold(st, lt, a, {"head": 12, "ua_f": 12, "fa_f": 60, "ua_b": -10, "fa_b": 80}, keep=a.get("keep", False))
    st.rot += 4 * w


def a_appear(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.2)
    k = clamp(lt / dur) if lt >= 0 else 0.0
    st.alpha *= smooth(k)
    st.scale *= lerp(0.86, 1.0, ease_back(k))
    st.glow = max(st.glow, 1.0 - k * 0.6 if lt < dur * 2 else 0.0)


def a_vanish(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.0)
    if lt < 0:
        return
    k = clamp(lt / dur)
    st.alpha *= 1 - smooth(k)
    st.glow = max(st.glow, k)
    st.dy -= 6 * k


def a_hidden(st, lt, a, rig, ctx):
    """Keep off-stage until a later action (use with appear)."""
    if lt < a.get("dur", 1e9):
        st.alpha = 0.0


def a_turn(st, lt, a, rig, ctx):
    dur = a.get("dur", 0.4)
    if lt < 0:
        return
    if lt < dur:
        k = lt / dur
        st.flipx = abs(math.cos(math.pi * k))
        if k >= 0.5:
            st.face = a.get("face_to", -st.face if "_face0" not in a else -a["_face0"])
    else:
        st.face = a.get("face_to", -a.get("_face0", st.face))


def a_grow(st, lt, a, rig, ctx):
    dur = a.get("dur", 2.0)
    if lt < 0:
        return
    st.scale *= lerp(1.0, a.get("to", 2.0), ease_in_out(lt / dur))
    st.glow = max(st.glow, 0.5 * _env(lt, dur + 1, 0.5))


def a_shrink(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.5)
    if lt < 0:
        return
    st.scale *= lerp(1.0, a.get("to", 0.4), ease_in_out(lt / dur))


def a_move(st, lt, a, rig, ctx):
    """Glide without walking (float / be carried / chariot)."""
    dur = a.get("dur", 2.0)
    x0 = a.get("_from", st.x)
    st.x = lerp(x0, a.get("to", x0), ease_in_out(lt / dur))
    if "dy" in a:
        st.dy += a["dy"] * ease_in_out(lt / dur)


def a_glow(st, lt, a, rig, ctx):
    dur = a.get("dur", 2.0)
    st.glow = max(st.glow, a.get("amount", 1.0) * _env(lt, dur, 0.4))


def a_spin(st, lt, a, rig, ctx):
    """Spin a held item (Sudarshan chakra!) — part name via `part`."""
    dur = a.get("dur", 3.0)
    if 0 <= lt <= dur:
        part = a.get("part", "it_x0" if "it_x0" in rig.parts else "it_f")
        st.add(part + ".w" if rig.parts.get(part) and rig.parts[part].world is not None else part,
               lt * a.get("speed", 720))


def a_pose(st, lt, a, rig, ctx):
    """Raw pose: {do: pose, angles: {ua_f: -90, fa_f: 0}, at, dur}"""
    _hold(st, lt, a, a.get("angles", {}), keep=a.get("keep", True))


def a_silhouette(st, lt, a, rig, ctx):
    if lt >= 0:
        st.silhouette = a.get("on", True)


# ---------------------------------------------------------------- animal-only

def a_graze(st, lt, a, rig, ctx):
    _hold(st, lt, a, {"head": 40}, keep=a.get("keep", False))


def a_rear(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.2)
    if 0 <= lt <= dur:
        w = math.sin(math.pi * lt / dur)
        st.rot -= 28 * w
        st.add("leg_fn", -50 * w)
        st.add("leg_ff", -40 * w)
        st.add("head", -15 * w)


def a_roar(st, lt, a, rig, ctx):
    dur = a.get("dur", 1.2)
    if 0 <= lt <= dur:
        w = _env(lt, dur, 0.2)
        st.add("head", (-18 + 3 * math.sin(lt * 30)) * w)
        st.shake = max(st.shake, 0.3 * w)


def a_peck(st, lt, a, rig, ctx):
    dur = a.get("dur", 2.0)
    if 0 <= lt <= dur:
        st.add("body", 18 * max(0, math.sin(lt * 7)) * _env(lt, dur, 0.1))


ACTIONS = {
    "walk": a_walk, "run": a_run, "talk": a_talk, "point": a_point, "bless": a_bless, "namaste": a_namaste,
    "pranam": a_namaste, "bow": a_bow, "raise": a_raise, "raise_weapon": a_raise, "raise_both": a_raise_both,
    "strike": a_strike, "attack": a_strike, "shoot": a_shoot, "shoot_arrow": a_shoot, "throw": a_throw,
    "fight": a_fight, "sit": a_sit, "stand": a_stand, "meditate": a_meditate, "fly": a_fly, "hover": a_hover,
    "jump": a_jump, "leap": a_jump, "fall": a_fall, "die": a_fall, "shake": a_shake, "angry": a_angry,
    "dance": a_dance, "laugh": a_laugh, "sad": a_sad, "appear": a_appear, "vanish": a_vanish, "hidden": a_hidden,
    "turn": a_turn, "grow": a_grow, "shrink": a_shrink, "move": a_move, "glide": a_move, "glow": a_glow,
    "spin": a_spin, "pose": a_pose, "silhouette": a_silhouette, "graze": a_graze, "rear": a_rear, "roar": a_roar,
    "peck": a_peck, "enter": a_walk, "exit": a_walk,
}

ACTION_HELP = {
    "walk": "to (x 0..1), dur, steps, face(auto|keep)", "run": "to, dur", "talk": "dur, gesture(bool)",
    "point": "dur, keep", "bless": "abhaya mudra; dur, keep", "namaste": "dur, keep", "bow": "deep pranam",
    "raise": "raise weapon arm", "raise_both": "both arms up (victory/prayer)", "strike": "mace/sword blow; dur",
    "shoot": "draw bow & release; dur", "throw": "throw spear/chakra", "fight": "repeated strikes; dur, period",
    "sit": "switch to seated (padmasana)", "stand": "back to standing", "meditate": "seated dhyana + aura",
    "fly": "to, dur, height, arc", "hover": "float in place; height", "jump": "height, dur, to",
    "fall": "collapse & lie (die/faint); back(bool)", "shake": "tremble; amount", "angry": "furious gesture",
    "dance": "bpm, dur", "laugh": "dur", "sad": "head down; keep", "appear": "divine entrance (fade+glow)",
    "vanish": "fade out upward", "hidden": "invisible until dur", "turn": "flip facing; face_to(1|-1)",
    "grow": "virat roop; to(scale), dur", "shrink": "to, dur", "move": "glide to x; dy", "glow": "aura; amount",
    "spin": "spin held chakra; part, speed", "pose": "raw angles dict", "silhouette": "on/off shadow-puppet look",
    "graze": "animal head down", "rear": "horse rears up", "roar": "lion/tiger roar", "peck": "bird pecks",
}


# ============================================================ idle (always on)

def idle(st, t, rig, seed=0.0):
    kind = rig.meta.get("kind")
    s = seed
    # pendulum sway of a string puppet hanging from its control bar
    sway = 1.1 * math.sin(t * 1.25 + s) + 0.5 * math.sin(t * 2.3 + s * 1.7)
    if st.walking or st.flying:
        sway *= 0.3
    st.rot += sway * (0.8 if kind == "humanoid" else 0.35)
    st.dx += -sway * 0.35
    st.dy += 0.35 * math.sin(t * 2.5 + s)
    if kind == "humanoid":
        st.add("head", 1.4 * math.sin(t * 0.9 + s * 2))
        st.add("ua_f", 2.4 * math.sin(t * 1.25 + s + 0.6))
        st.add("fa_f", 3.0 * math.sin(t * 1.25 + s + 1.1))
        st.add("ua_b", -2.0 * math.sin(t * 1.25 + s + 0.4))
        st.add("fa_b", 2.0 * math.sin(t * 1.25 + s + 0.9))
        if "tail" in rig.parts:
            st.add("tail", 6 * math.sin(t * 1.6 + s))
        if "wing_f" in rig.parts:
            st.add("wing_f", 4 * math.sin(t * 1.9 + s))
            st.add("wing_b", 4 * math.sin(t * 1.9 + s + 0.4))
    elif kind == "quadruped":
        st.add("head", 2.0 * math.sin(t * 0.8 + s))
        st.add("tail", 8 * math.sin(t * 1.4 + s))
    elif kind == "bird" and not st.flying:
        st.add("body", 2.5 * max(0, math.sin(t * 1.6 + s)) ** 3 * 4)
        st.add("tail", 3 * math.sin(t * 2.0 + s))
    elif kind == "serpent":
        st.rot += 1.6 * math.sin(t * 1.4 + s)
    if st.shake > 0:
        st.dx += st.shake * 0.9 * math.sin(t * 61)
        st.rot += st.shake * 1.5 * math.sin(t * 47)


def evaluate(rig, x0, face0, mode0, actions, t, seed=0.0):
    """Compute the performer State at shot time t."""
    st = State(x=x0, face=face0, mode=mode0)
    x_cur, face_cur = x0, face0
    for a in actions:
        at = float(a.get("at", 0.0))
        if t < at:
            # a future 'hidden'/'appear' must still hide us before it starts
            if a.get("do") == "appear":
                st.alpha = 0.0
            continue
        fn = ACTIONS.get(a.get("do"))
        if not fn:
            continue
        a = dict(a)
        a.setdefault("_from", st.x)
        a.setdefault("_face0", st.face)
        fn(st, t - at, a, rig, None)
    idle(st, t, rig, seed)
    # mode-dependent visibility
    if rig.meta.get("kind") == "humanoid":
        if st.mode in ("seated",) and "lap" in rig.parts:
            st.hidden |= {"leg_f", "leg_b", "waist", "skirt"}
            st.show |= {"lap"}
    return st
