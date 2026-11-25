"""Procedural SFX library (royalty-free, generated) + user overrides.

Drop a real recording named <sfx>.wav/.mp3 into <project>/sfx/ (or
~/.cache/mythic25d/sfx_user/) and it replaces the synthetic one automatically.
`get_sfx(name, dur=None)` -> stereo float32 array at 44.1 kHz.
"""
from __future__ import annotations

import math
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

from .music import SR, additive, bandnoise, bell, drum, tabla_stroke, _t
from .util import CACHE_DIR


def _st(x, pan=0.0):
    x = np.asarray(x, np.float32)
    return np.stack([x * (1 - max(0, pan)), x * (1 + min(0, pan))], axis=1)


def _env(n, a=0.01, r=0.3):
    t = _t(n)
    dur = n / SR
    return np.minimum(1, t / max(1e-3, a)) * np.clip((dur - t) / max(1e-3, r), 0, 1)


def _norm(x, peak=0.9):
    return x / (np.abs(x).max() + 1e-9) * peak


def whoosh(dur=0.7, lo=300, hi=3000, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, lo, hi, seed)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return _norm(x * env)


def impact(dur=1.6, f=55):
    n = int(dur * SR)
    t = _t(n)
    fr = f * (1 - 0.5 * np.clip(t / 0.4, 0, 1))
    x = np.sin(np.cumsum(2 * np.pi * fr / SR)) * np.exp(-t / 0.5)
    x[: int(0.05 * SR)] += bandnoise(int(0.05 * SR), 200, 4000, 1) * 0.8
    x += bandnoise(n, 60, 400, 2) * np.exp(-t / 0.6) * 0.4
    return _norm(x)


def metal_hit(dur=1.2, f=520, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = np.zeros(n, np.float32)
    for r, a, d in ((1, 1, 0.5), (2.41, 0.7, 0.35), (3.9, 0.5, 0.25), (5.7, 0.35, 0.15), (7.3, 0.2, 0.1)):
        x += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    x[: int(0.01 * SR)] += bandnoise(int(0.01 * SR), 2000, 9000, seed)
    return _norm(x)


def crackle(dur=4.0, density=40, seed=0):
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    x = bandnoise(n, 200, 1200, seed) * 0.15
    for _ in range(int(density * dur)):
        s = r.integers(0, max(1, n - 400))
        L = r.integers(40, 400)
        x[s:s + L] += r.uniform(-1, 1) * np.exp(-np.arange(L) / (L / 4)) * r.uniform(0.3, 1)
    return _norm(x, 0.7)


def wind(dur=6.0, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 200, 1500, seed)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * t + seed) * np.sin(2 * np.pi * 0.05 * t)
    return _norm(x * mod, 0.6)


def birds(dur=6.0, seed=0):
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    x = wind(dur, seed) * 0.15
    for _ in range(int(dur * 2.2)):
        s = r.integers(0, max(1, n - SR))
        L = int(r.uniform(0.06, 0.18) * SR)
        f0 = r.uniform(2500, 5200)
        tt = _t(L)
        sweep = f0 * (1 + r.uniform(-0.3, 0.3) * tt / tt[-1])
        chirp = np.sin(np.cumsum(2 * np.pi * sweep / SR)) * np.sin(np.pi * tt / tt[-1])
        for k in range(r.integers(1, 4)):
            o = s + int(k * L * 1.3)
            if o + L < n:
                x[o:o + L] += chirp * r.uniform(0.2, 0.5)
    return _norm(x, 0.6)


def crickets(dur=6.0, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = np.zeros(n, np.float32)
    for k, f in enumerate((4400, 4700, 5100)):
        gate = (np.sin(2 * np.pi * (18 + k * 3) * t) > 0.3) * (np.sin(2 * np.pi * (0.8 + k * 0.3) * t + k) > -0.2)
        x += np.sin(2 * np.pi * f * t) * gate * 0.3
    return _norm(x, 0.45)


def waves(dur=8.0, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 150, 2500, seed)
    swell = 0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 5.5 + seed)) ** 2
    return _norm(x * swell, 0.7)


def river(dur=6.0, seed=0):
    n = int(dur * SR)
    x = bandnoise(n, 400, 5000, seed)
    r = np.random.default_rng(seed)
    for _ in range(int(dur * 25)):
        s = r.integers(0, n - 2000)
        L = 1500
        tt = _t(L)
        x[s:s + L] += np.sin(2 * np.pi * r.uniform(600, 1800) * tt * (1 + tt * 8)) * np.exp(-tt / 0.01) * 0.6
    return _norm(x, 0.55)


def rain(dur=6.0, seed=0):
    return _norm(bandnoise(int(dur * SR), 800, 8000, seed) * 0.8 + crackle(dur, 120, seed) * 0.3, 0.6)


def thunder(dur=4.0, seed=0, soft=False):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 30, 400, seed) * np.exp(-t / (1.4 if not soft else 0.8))
    x[: int(0.2 * SR)] += bandnoise(int(0.2 * SR), 300, 3000, seed + 1) * (0.8 if not soft else 0.3)
    rumble = np.sin(2 * np.pi * 0.7 * t) * 0.5 + 0.5
    return _norm(x * (0.6 + 0.4 * rumble), 0.95 if not soft else 0.6)


def conch(dur=3.2):
    n = int(dur * SR)
    t = _t(n)
    f = 233 * (1 + 0.012 * np.sin(2 * np.pi * 5 * t)) * (1 + 0.04 * np.clip(t / 0.4, 0, 1))
    ph = np.cumsum(2 * np.pi * f / SR)
    x = sum(a * np.sin(k * ph) for k, a in ((1, 1), (2, 0.8), (3, 0.6), (4, 0.4), (5, 0.25), (6, 0.15)))
    x += bandnoise(n, 800, 3000, 3) * 0.08
    env = np.minimum(1, t / 0.35) * np.clip((dur - t) / 0.8, 0, 1)
    return _norm(x * env)


def shimmer(dur=2.5, seed=0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    r = np.random.default_rng(seed)
    for k in range(18):
        s = int(r.uniform(0, dur * 0.6) * SR)
        b = bell(r.choice([1320, 1760, 2093, 2637, 3136]), dur, 0.3)
        x[s:] += b[: n - s]
    t = _t(n)
    x += bandnoise(n, 3000, 9000, seed) * 0.1 * np.sin(np.pi * t / dur)
    return _norm(x, 0.7)


def swell(dur=2.5, seed=0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 200, 4000, seed) * (t / dur) ** 2
    x += np.sin(2 * np.pi * (110 + 220 * t / dur) * t) * (t / dur) * 0.4
    return _norm(x * np.clip((dur - t) / 0.2, 0, 1), 0.8)


def footsteps(dur=2.0, rate=2.2, seed=0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    k = 0
    while k / rate < dur:
        s = int(k / rate * SR)
        L = int(0.12 * SR)
        if s + L < n:
            x[s:s + L] += bandnoise(L, 80, 900, k) * np.exp(-_t(L) / 0.03) * (0.8 if k % 2 else 0.6)
        k += 1
    return _norm(x, 0.6)


def gallop(dur=3.0, seed=0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    beat = 0.36
    k = 0
    while k * beat < dur:
        for j, off in enumerate((0, 0.07, 0.14)):
            s = int((k * beat + off) * SR)
            L = int(0.08 * SR)
            if s + L < n:
                x[s:s + L] += bandnoise(L, 100, 1200, k * 3 + j) * np.exp(-_t(L) / 0.02)
        k += 1
    return _norm(x, 0.8)


def murmur(dur=6.0, seed=0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    for k in range(6):
        v = bandnoise(n, 250 + k * 60, 1100 + k * 100, seed + k)
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * (2.5 + k * 0.7) * _t(n) + k)
        x += v * mod * 0.3
    return _norm(x, 0.5)


def creature_call(dur=1.4, f0=420, f1=900, formants=(700, 1200), seed=0, rough=0.3):
    n = int(dur * SR)
    t = _t(n)
    k = t / dur
    f = f0 + (f1 - f0) * np.sin(np.pi * k) + 30 * np.sin(2 * np.pi * 9 * t)
    ph = np.cumsum(2 * np.pi * f / SR)
    x = sum(np.sin(m * ph) / m for m in range(1, 9))
    x += rough * bandnoise(n, *formants, seed)
    env = np.minimum(1, t / 0.05) * np.clip((dur - t) / 0.3, 0, 1)
    return _norm(x * env)


def laugh(dur=2.0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    for k in range(7):
        s = int(k * 0.24 * SR)
        L = int(0.18 * SR)
        if s + L < n:
            x[s:s + L] += creature_call(0.18, 130 - k * 4, 160 - k * 6, (300, 900), k, 0.5)
    return _norm(x)


def drone(dur=6.0, f=55):
    n = int(dur * SR)
    t = _t(n)
    x = sum(np.sin(2 * np.pi * f * m * (1 + 0.002 * m) * t) / m for m in range(1, 7))
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    return _norm(x, 0.5)


def chakra_spin(dur=2.0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 800, 6000, 4) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * t))
    x += np.sin(2 * np.pi * (600 + 300 * np.sin(2 * np.pi * 3 * t)) * t) * 0.3
    return _norm(x * np.sin(np.pi * t / dur), 0.7)


def war_drums(dur=6.0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    beat = 0.45
    k = 0
    pattern = ["boom", "-", "slap", "boom", "boom", "slap", "roll", "-"]
    while k * beat < dur:
        p = pattern[k % len(pattern)]
        if p != "-":
            d = drum(p)
            s = int(k * beat * SR)
            x[s:s + len(d)] += d[: n - s]
        k += 1
    return _norm(x, 0.8)


def string_creak(dur=0.6):
    n = int(dur * SR)
    t = _t(n)
    f = 180 + 90 * np.sin(2 * np.pi * 2 * t)
    x = np.sign(np.sin(np.cumsum(2 * np.pi * f / SR))) * bandnoise(n, 600, 2400, 9) * 0.5
    return _norm(x * np.sin(np.pi * t / dur), 0.4)


def curtain(dur=2.4):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 300, 5000, 2) * np.sin(np.pi * t / dur) ** 1.5
    x += string_creak(dur) * 0.2
    return _norm(x, 0.7)


def ghanta_ring(dur=4.0):
    x = bell(880, dur, 1.0)
    return _norm(x + np.roll(x, int(0.45 * SR)) * 0.6)


def temple_bells(dur=6.0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    for k in range(int(dur / 1.4)):
        b = bell([660, 880, 990][k % 3], 3.0, 0.5)
        s = int(k * 1.4 * SR)
        x[s:s + len(b)] += b[: n - s]
    return _norm(x + murmur(dur) * 0.2, 0.6)


def damru_roll(dur=1.6):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    k = 0
    while k * 0.07 < dur:
        d = tabla_stroke("ti", 420)
        s = int(k * 0.07 * SR)
        x[s:s + len(d)] += d[: n - s] * (0.6 + 0.4 * (k % 2))
        k += 1
    return _norm(x)


def body_fall():
    return _norm(impact(0.9, 70) * 0.7 + whoosh(0.3, 200, 900, 4)[: int(0.9 * SR)].mean() * 0)


def splash(dur=1.5):
    n = int(dur * SR)
    t = _t(n)
    return _norm(bandnoise(n, 400, 7000, 6) * np.exp(-t / 0.35) + river(dur) * 0.2)


def heartbeat(dur=3.0, bpm=60):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    k = 0
    while k * 60 / bpm < dur:
        for off, a in ((0, 1.0), (0.22, 0.7)):
            d = drum("boom")[: int(0.3 * SR)] * a
            s = int((k * 60 / bpm + off) * SR)
            x[s:s + len(d)] += d[: n - s]
        k += 1
    return _norm(x, 0.8)


def arrows_volley(dur=2.0):
    n = int(dur * SR)
    x = np.zeros(n, np.float32)
    r = np.random.default_rng(3)
    for k in range(14):
        w = whoosh(0.35, 1200, 6000, k)
        s = int(r.uniform(0, dur - 0.4) * SR)
        x[s:s + len(w)] += w * r.uniform(0.3, 0.8)
    return _norm(x, 0.8)


def crowd_cheer(dur=3.0):
    n = int(dur * SR)
    t = _t(n)
    return _norm(murmur(dur, 5) * (0.4 + 0.6 * np.sin(np.pi * t / dur)) + bandnoise(n, 600, 3000, 4) * 0.3, 0.8)


def chariot(dur=4.0):
    n = int(dur * SR)
    t = _t(n)
    x = bandnoise(n, 40, 300, 8) * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * t))
    return _norm(x * 0.7 + gallop(dur) * 0.6, 0.8)


GEN = {
    "whoosh": lambda d: whoosh(d or 0.6), "whoosh_long": lambda d: whoosh(d or 1.6, 150, 2000, 2),
    "arrow_whoosh": lambda d: whoosh(d or 0.45, 1500, 7000, 3), "arrows_volley": lambda d: arrows_volley(d or 2.0),
    "impact_boom": lambda d: impact(d or 1.8), "mace_hit": lambda d: _norm(impact(0.9, 90) * 0.6 + metal_hit(0.9, 300) * 0.5),
    "sword_clash": lambda d: metal_hit(d or 1.0, 780), "body_fall": lambda d: body_fall(),
    "thunder": lambda d: thunder(d or 4.0), "thunder_soft": lambda d: thunder(d or 2.0, soft=True),
    "earthquake": lambda d: _norm(thunder(d or 3.0, 5) + drone(d or 3.0, 35) * 0.6),
    "conch": lambda d: conch(d or 3.2), "shankh": lambda d: conch(d or 3.2), "bell_soft": lambda d: bell(1320, d or 2.5, 0.6),
    "ghanta": lambda d: ghanta_ring(d or 4.0), "temple_bells": lambda d: temple_bells(d or 6.0),
    "divine_shimmer": lambda d: shimmer(d or 2.5), "magic_swell": lambda d: swell(d or 2.2),
    "divine_pad": lambda d: _norm(drone(d or 6.0, 110) * 0.6 + shimmer(min(d or 6.0, 6.0)) * 0.3, 0.5),
    "cosmic_drone": lambda d: drone(d or 6.0, 41), "chakra_spin": lambda d: chakra_spin(d or 2.0),
    "fire_crackle": lambda d: crackle(d or 5.0, 30), "fire_big": lambda d: _norm(crackle(d or 5.0, 90) + wind(d or 5.0) * 0.5),
    "campfire": lambda d: _norm(crackle(d or 5.0, 25) + crickets(d or 5.0) * 0.4, 0.6),
    "wind": lambda d: wind(d or 6.0), "forest_birds": lambda d: birds(d or 6.0), "crickets": lambda d: crickets(d or 6.0),
    "ocean_waves": lambda d: waves(d or 8.0), "river": lambda d: river(d or 6.0), "rain_storm": lambda d: rain(d or 6.0),
    "cave_drips": lambda d: _norm(drone(d or 6.0, 60) * 0.3 + river(d or 6.0) * 0.15, 0.4),
    "palace_hum": lambda d: _norm(murmur(d or 6.0) * 0.4 + drone(d or 6.0, 98) * 0.2, 0.35),
    "audience_murmur": lambda d: murmur(d or 6.0), "village": lambda d: _norm(birds(d or 6.0) * 0.5 + murmur(d or 6.0) * 0.3, 0.5),
    "battle_ambience": lambda d: _norm(war_drums(d or 6.0) * 0.5 + murmur(d or 6.0, 9) * 0.5 + wind(d or 6.0) * 0.3, 0.7),
    "war_drums": lambda d: war_drums(d or 6.0), "footsteps": lambda d: footsteps(d or 2.0),
    "footsteps_fast": lambda d: footsteps(d or 1.5, 4.0), "horse_gallop": lambda d: gallop(d or 3.0),
    "chariot_rumble": lambda d: chariot(d or 4.0), "horse_neigh": lambda d: creature_call(d or 1.3, 600, 1200, (900, 2500), 1, 0.4),
    "elephant_trumpet": lambda d: creature_call(d or 1.6, 380, 720, (500, 1800), 2, 0.6),
    "roar": lambda d: creature_call(d or 1.6, 90, 140, (200, 900), 3, 1.2), "demon_laugh": lambda d: laugh(d or 2.0),
    "crow_caw": lambda d: creature_call(d or 0.45, 700, 650, (900, 2600), 4, 0.9),
    "peacock_call": lambda d: creature_call(d or 0.9, 900, 1600, (1200, 3000), 5, 0.3),
    "curtain_swish": lambda d: curtain(d or 2.4), "string_creak": lambda d: string_creak(d or 0.6),
    "damru": lambda d: damru_roll(d or 1.6), "splash": lambda d: splash(d or 1.5), "heartbeat": lambda d: heartbeat(d or 3.0),
    "crowd_cheer": lambda d: crowd_cheer(d or 3.0), "gong": lambda d: _norm(metal_hit(d or 5.0, 110) * 0.8 + drone(d or 5.0, 55) * 0.2),
    "nagara": lambda d: _norm(drum("boom") * 1.0 + np.pad(drum("boom"), (int(0.3 * SR), 0))[: SR] * 0.8),
}
DESCRIPTIONS = {k: k.replace("_", " ") for k in GEN}


def _user_file(name, extra_dirs=()):
    for d in list(extra_dirs) + [CACHE_DIR / "sfx_user"]:
        for ext in (".wav", ".mp3", ".ogg", ".flac", ".m4a"):
            p = Path(d) / f"{name}{ext}"
            if p.exists():
                return p
    return None


def _decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


@lru_cache(maxsize=128)
def _gen(name, dur):
    if name not in GEN:
        raise KeyError(f"unknown sfx '{name}'. Run: mythic.py list sfx")
    return _st(GEN[name](dur))


def get_sfx(name, dur=None, extra_dirs=()):
    p = _user_file(name, extra_dirs)
    if p:
        x = _decode(p)
        if dur and len(x) < dur * SR:  # loop beds
            reps = int(math.ceil(dur * SR / len(x)))
            x = np.tile(x, (reps, 1))
        return x[: int(dur * SR)] if dur else x
    d = None if dur is None else round(float(dur), 2)
    if d and d > 12 and name in GEN:
        # long beds: loop a 12s render with crossfade
        base = _gen(name, 12.0)
        reps = int(math.ceil(d / 11.0))
        out = np.zeros((int(d * SR) + SR, 2), np.float32)
        fade = int(SR * 1.0)
        w = np.linspace(0, 1, fade)[:, None]
        for k in range(reps):
            s = int(k * 11.0 * SR)
            seg = base.copy()
            seg[:fade] *= w
            seg[-fade:] *= w[::-1]
            e = min(len(out), s + len(seg))
            out[s:e] += seg[: e - s]
        return out[: int(d * SR)]
    return _gen(name, d)
