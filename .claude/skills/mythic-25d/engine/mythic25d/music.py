"""Procedural Indian-classical score: tanpura drone + raga melody + tala.

`render_music(sections, total, out_wav)` where sections = [{at, mood, raga}].
Moods pick raga, tempo, lead instrument, percussion and intensity.  It's a
royalty-free *temp/bed* score; swap in a licensed track any time with
`music: {file: path}` in the storyboard.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SR = 44100

RAGAS = {
    "yaman": ([0, 2, 4, 6, 7, 9, 11], 4, 11), "bhupali": ([0, 2, 4, 7, 9], 4, 9), "bhairav": ([0, 1, 4, 5, 7, 8, 11], 8, 1),
    "bhairavi": ([0, 1, 3, 5, 7, 8, 10], 5, 0), "darbari": ([0, 2, 3, 5, 7, 8, 10], 2, 7), "malkauns": ([0, 3, 5, 8, 10], 5, 0),
    "marwa": ([0, 1, 4, 6, 9, 11], 1, 4), "desh": ([0, 2, 4, 5, 7, 9, 10, 11], 2, 7), "durga": ([0, 2, 5, 7, 9], 5, 0),
    "bageshree": ([0, 2, 3, 5, 7, 9, 10], 5, 0), "kirwani": ([0, 2, 3, 5, 7, 8, 11], 7, 0), "shivaranjani": ([0, 2, 3, 7, 9], 3, 9),
    "todi": ([0, 1, 3, 6, 7, 8, 11], 8, 3), "hamsadhwani": ([0, 2, 4, 7, 11], 4, 11), "kafi": ([0, 2, 3, 5, 7, 9, 10], 7, 0),
    "puriya_dhanashri": ([0, 1, 4, 6, 7, 8, 11], 7, 1),
}

MOODS = {
    #            raga        bpm  lead       perc        intensity  pad   tala
    "devotional": ("yaman", 72, "bansuri", "tabla", 0.55, False, "teental"),
    "divine": ("bhairav", 60, "bansuri", "none", 0.45, True, "teental"),
    "epic_battle": ("kirwani", 118, "shehnai", "dhol", 0.95, True, "battle"),
    "battle": ("kirwani", 118, "shehnai", "dhol", 0.95, True, "battle"),
    "mystery": ("malkauns", 54, "santoor", "none", 0.4, True, "teental"),
    "sorrow": ("bhairavi", 56, "sarangi", "tabla_soft", 0.35, False, "dadra"),
    "sad": ("shivaranjani", 56, "sarangi", "tabla_soft", 0.35, False, "dadra"),
    "forest": ("desh", 80, "bansuri", "tabla_soft", 0.45, False, "keherwa"),
    "royal": ("durga", 92, "shehnai", "tabla", 0.7, False, "teental"),
    "tension": ("marwa", 100, "santoor", "pulse", 0.75, True, "keherwa"),
    "triumph": ("durga", 112, "shehnai", "dhol", 0.9, True, "keherwa"),
    "night": ("bageshree", 62, "sitar", "tabla_soft", 0.4, False, "teental"),
    "auspicious": ("hamsadhwani", 86, "shehnai", "tabla", 0.6, False, "keherwa"),
    "dance": ("desh", 124, "santoor", "dhol", 0.85, False, "keherwa"),
    "meditative": ("yaman", 50, "sitar", "none", 0.3, True, "teental"),
    "romance": ("kafi", 76, "bansuri", "tabla_soft", 0.5, False, "dadra"),
    "dawn": ("bhairav", 66, "bansuri", "tabla_soft", 0.45, False, "teental"),
}
TALAS = {"teental": ["dha", "dhin", "dhin", "dha", "dha", "dhin", "dhin", "dha", "dha", "tin", "tin", "ta", "ta", "dhin", "dhin", "dha"],
         "keherwa": ["dha", "ge", "na", "ti", "na", "ka", "dhin", "na"],
         "dadra": ["dha", "dhin", "na", "dha", "tin", "na"],
         "battle": ["boom", "-", "slap", "boom", "boom", "-", "slap", "-", "boom", "-", "slap", "boom", "boom", "slap", "roll", "roll"]}


def _t(n):
    return np.arange(n, dtype=np.float32) / SR


def additive(freq, dur, partials=10, decay=1.5, bright=0.6, inharm=0.0, bloom=0.0, attack=0.004):
    n = int(dur * SR)
    t = _t(n)
    out = np.zeros(n, np.float32)
    for k in range(1, partials + 1):
        f = freq * k * (1 + inharm * k * k)
        if f > SR * 0.45:
            break
        amp = 1.0 / k ** (1.6 - bright)
        dk = decay * (1 + 0.35 * (k - 1))
        env = np.exp(-t * dk)
        if bloom:
            env = env * (1 + bloom * (k / partials) * np.sin(np.pi * np.clip(t / max(0.1, dur), 0, 1)))
        out += amp * env * np.sin(2 * np.pi * f * t + k * 0.7)
    a = int(attack * SR)
    if a > 1:
        out[:a] *= np.linspace(0, 1, a)
    return out


def bandnoise(n, lo, hi, seed=0):
    r = np.random.default_rng(seed)
    x = r.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.exp(-((np.log(np.maximum(f, 1) / math.sqrt(lo * hi))) / (0.5 * math.log(hi / lo) + 1e-3)) ** 2)
    y = np.fft.irfft(X * m, n).astype(np.float32)
    return y / (np.abs(y).max() + 1e-9)


def glide_osc(freqs, harmonics, vib=0.0, vib_rate=5.2, seed=0):
    """Phase-continuous oscillator following a per-sample frequency curve."""
    n = len(freqs)
    t = _t(n)
    f = freqs * (1 + vib * np.sin(2 * np.pi * vib_rate * t))
    ph = np.cumsum(2 * np.pi * f / SR)
    out = np.zeros(n, np.float32)
    for k, a in enumerate(harmonics, 1):
        out += a * np.sin(k * ph)
    return out


# --------------------------------------------------------------- instruments

def tanpura(base, dur, pattern=(7, 12, 12, 0), cycle=4.4, seed=0):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    step = cycle / len(pattern)
    t0, i = 0.0, 0
    while t0 < dur:
        semi = pattern[i % len(pattern)]
        f = base * 2 ** ((semi - (12 if semi >= 12 else 0) - 12) / 12.0) * (2 if semi >= 12 else 1)
        note = additive(f, min(cycle * 1.6, dur - t0 + 0.01), partials=14, decay=0.55, bright=0.95, bloom=1.6, attack=0.01)
        s = int(t0 * SR)
        e = min(n, s + len(note))
        out[s:e] += note[: e - s] * (0.9 if semi in (0, 12) else 0.75)
        t0 += step
        i += 1
    return out


def lead_note(inst, f0, f1, dur, seed=0):
    n = int(dur * SR)
    if n < 10:
        return np.zeros(max(1, n), np.float32)
    t = _t(n)
    if inst in ("bansuri", "sarangi", "shehnai"):
        glide = np.clip(t / max(0.05, dur * 0.3), 0, 1)
        freqs = f0 + (f1 - f0) * (glide * glide * (3 - 2 * glide)) if f0 != f1 else np.full(n, f1, np.float32)
        vib = np.clip((t - 0.25) / 0.6, 0, 1) * (0.006 if inst == "bansuri" else 0.011)
        if inst == "bansuri":
            y = glide_osc(freqs, [1.0, 0.18, 0.06, 0.02], vib=0, vib_rate=5.0)
            y = glide_osc(freqs * (1 + vib * np.sin(2 * np.pi * 5.0 * t)), [1.0, 0.18, 0.06, 0.02])
            y += 0.06 * bandnoise(n, 1500, 6000, seed) * np.clip(1.2 - t / 0.4, 0.3, 1)
            att, rel = 0.07, 0.12
        elif inst == "shehnai":
            y = glide_osc(freqs * (1 + vib * np.sin(2 * np.pi * 6.0 * t)), [1, 0.7, 0.55, 0.45, 0.35, 0.25, 0.18, 0.12])
            att, rel = 0.03, 0.08
        else:  # sarangi: bowed, nasal
            y = glide_osc(freqs * (1 + vib * 1.3 * np.sin(2 * np.pi * 5.5 * t)), [1, 0.5, 0.42, 0.3, 0.22, 0.16])
            y += 0.04 * bandnoise(n, 2000, 7000, seed)
            att, rel = 0.12, 0.2
        env = np.minimum(1, t / att) * np.minimum(1, np.maximum(0, (dur - t) / rel))
        return (y * env).astype(np.float32)
    if inst == "santoor":
        y = additive(f1, dur + 0.8, partials=9, decay=2.2, bright=1.05, inharm=0.0004)
        if dur > 0.6:  # tremolo re-strikes on long notes
            k = 1
            while k * 0.12 < dur - 0.2:
                s = int(k * 0.12 * SR)
                y2 = additive(f1, dur + 0.8 - k * 0.12, partials=8, decay=2.6, bright=1.0) * 0.55
                y[s:s + len(y2)] += y2[: len(y) - s]
                k += 1
        return y[:n + int(0.8 * SR)]
    if inst == "sitar":
        y = additive(f1, dur + 1.2, partials=14, decay=1.1, bright=1.15, inharm=0.0002, bloom=0.8)
        y += 0.25 * additive(f1 * 2, dur + 1.2, partials=6, decay=0.8, bright=1.0)
        return y
    return additive(f1, dur, decay=2.0)


def tabla_stroke(bol, sa, soft=False):
    n = int(0.9 * SR)
    t = _t(n)
    v = 0.55 if soft else 1.0
    out = np.zeros(n, np.float32)

    def dayan(ring=0.25, amp=1.0):
        return amp * (np.sin(2 * np.pi * sa * 2 * t) + 0.45 * np.sin(2 * np.pi * sa * 2 * 2.02 * t) +
                      0.25 * np.sin(2 * np.pi * sa * 2 * 3.01 * t)) * np.exp(-t / ring)

    def bayan(amp=1.0):
        f = 95 * (1 - 0.32 * np.clip(t / 0.25, 0, 1))
        return amp * np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.32)

    if bol in ("dha", "dhin"):
        out += dayan(0.32 if bol == "dhin" else 0.18) * 0.7 + bayan(0.9)
    elif bol in ("ta", "na", "tin", "ti"):
        out += dayan(0.22 if bol == "tin" else 0.1, 0.8)
    elif bol == "ge":
        out += bayan(1.0)
    elif bol == "ka":
        out[: int(0.04 * SR)] += bandnoise(int(0.04 * SR), 200, 900, 3) * 0.6
    out[: int(0.006 * SR)] += bandnoise(int(0.006 * SR), 2000, 8000, 5) * 0.4
    return out * v


def drum(kind):
    n = int(1.0 * SR)
    t = _t(n)
    if kind == "boom":
        f = 70 * (1 - 0.45 * np.clip(t / 0.3, 0, 1))
        y = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.42)
        y[: int(0.02 * SR)] += bandnoise(int(0.02 * SR), 100, 1200, 1) * 0.6
        return y * 1.2
    if kind == "slap":
        y = bandnoise(n, 500, 3500, 2) * np.exp(-t / 0.08) * 0.8
        y += np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.1) * 0.5
        return y
    if kind == "roll":
        y = np.zeros(n, np.float32)
        for k in range(4):
            s = int(k * 0.06 * SR)
            y[s:] += (bandnoise(n - s, 300, 2500, k) * np.exp(-_t(n - s) / 0.05) * 0.5)[: n - s]
        return y
    return np.zeros(n, np.float32)


def bell(f=880, dur=4.0, amp=0.6):
    n = int(dur * SR)
    t = _t(n)
    y = np.zeros(n, np.float32)
    for r, a, d in ((1, 1, 2.4), (2.76, 0.6, 1.6), (5.4, 0.35, 0.9), (8.93, 0.2, 0.5), (13.3, 0.1, 0.3)):
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return y * amp


def pad(base, dur, scale, seed=0):
    """Soft choir/strings bed on Sa-Pa-Sa' (with the raga's 3rd if present)."""
    n = int(dur * SR)
    t = _t(n)
    y = np.zeros(n, np.float32)
    third = 4 if 4 in scale else (3 if 3 in scale else 5)
    for semi, a in ((0, 0.5), (7, 0.4), (12, 0.35), (12 + third, 0.2)):
        f = base * 2 ** (semi / 12)
        for det in (-0.004, 0.0, 0.0045):
            ph = 2 * np.pi * f * (1 + det) * t
            y += a * (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) / 3
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + seed)
    fade = np.minimum(1, t / 3.0) * np.minimum(1, (dur - t) / 3.0)
    return y * lfo * np.clip(fade, 0, 1)


# --------------------------------------------------------------- composition

def melody(scale, vadi, samvadi, beats, rng):
    """Phrase-based raga improvisation -> list of (beat_start, beat_len, semitone|None)."""
    deg = sorted(set(scale + [s + 12 for s in scale] + [s - 12 for s in scale if s >= 5]))
    deg = [d for d in deg if -7 <= d <= 19]
    home = deg.index(0)
    i = home
    out, b = [], 0.0
    while b < beats:
        plen = rng.choice([4, 6, 8])
        pb = 0.0
        while pb < plen and b + pb < beats:
            L = rng.choice([0.5, 0.5, 1, 1, 1, 1.5, 2])
            step = rng.choice([-2, -1, -1, 1, 1, 2, 0])
            i = max(0, min(len(deg) - 1, i + step))
            if rng.random() < 0.12:
                target = vadi if rng.random() < 0.6 else samvadi
                cands = [k for k, d in enumerate(deg) if d % 12 == target % 12]
                if cands:
                    i = min(cands, key=lambda k: abs(k - i))
            out.append((b + pb, L, deg[i]))
            pb += L
        # resolve phrase on Sa / Pa / vadi with a long note, then breathe
        ends = [k for k, d in enumerate(deg) if d % 12 in (0, 7, vadi % 12)]
        i = min(ends, key=lambda k: abs(k - i))
        out.append((b + pb, rng.choice([2, 3]), deg[i]))
        b += pb + rng.choice([3, 4, 4, 5])
    return out


def section_audio(mood, raga, dur, base=138.59, seed=0):
    m = MOODS.get(mood, MOODS["devotional"])
    raga = raga or m[0]
    scale, vadi, samvadi = RAGAS.get(raga, RAGAS["yaman"])
    bpm, lead, perc, inten, use_pad, tala = m[1], m[2], m[3], m[4], m[5], m[6]
    rng = np.random.default_rng(seed)
    import random as _r
    pr = _r.Random(seed)
    n = int(dur * SR)
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)

    def add(sig, at, gl, gr):
        s = int(at * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        L[s:e] += sig[: e - s] * gl
        R[s:e] += sig[: e - s] * gr

    pa_or_ma = 7 if 7 in scale else 5
    drone = tanpura(base, dur, (pa_or_ma, 12, 12, 0), cycle=4.4 * 60 / max(50, bpm) * 1.2 + 2.0)
    add(drone * 0.16, 0, 1.0, 0.85)
    add(tanpura(base * 1.003, dur, (pa_or_ma, 12, 12, 0), cycle=4.7) * 0.1, 0.9, 0.8, 1.0)
    if use_pad or mood in ("divine", "mystery"):
        add(pad(base, dur, scale, seed) * 0.05, 0, 0.9, 0.9)
    beat = 60.0 / bpm
    intro = min(dur * 0.22, 12.0) if perc != "none" else dur
    # melody
    lead_base = base * 2 if lead in ("bansuri", "shehnai", "santoor") else base
    gain = {"bansuri": 0.22, "shehnai": 0.14, "sarangi": 0.16, "santoor": 0.2, "sitar": 0.2}.get(lead, 0.2)
    notes = melody(scale, vadi, samvadi, int(dur / beat), pr)
    prev = None
    for b0, bl, semi in notes:
        at = b0 * beat
        if at > dur - 1.0:
            break
        f1 = lead_base * 2 ** (semi / 12)
        f0 = prev if prev and pr.random() < 0.45 else f1
        sig = lead_note(lead, f0, f1, bl * beat * (1.0 if at < intro else 0.92), seed=int(b0 * 10))
        sp = 0.5 + 0.15 * math.sin(b0 * 0.3)
        add(sig * gain * (0.8 if at < intro else 1.0), at, 1 - sp * 0.4, 0.6 + sp * 0.4)
        prev = f1
    # percussion
    if perc != "none":
        bols = TALAS.get(tala, TALAS["teental"])
        t0 = intro
        k = 0
        while t0 < dur - 0.5:
            bol = bols[k % len(bols)]
            fade = min(1.0, (t0 - intro) / 4.0)
            if perc in ("tabla", "tabla_soft"):
                if bol != "-":
                    add(tabla_stroke(bol, base * 2, soft=perc == "tabla_soft") * 0.22 * fade * (1.15 if k % len(bols) == 0 else 1),
                        t0, 0.9, 1.0)
                if perc == "tabla" and inten > 0.6 and pr.random() < 0.18:
                    add(tabla_stroke("ti", base * 2) * 0.12 * fade, t0 + beat / 2, 0.9, 1.0)
            elif perc == "dhol":
                if bol != "-":
                    add(drum(bol) * 0.3 * fade, t0, 1.0, 0.95)
                if k % 2 == 1:
                    add(drum("slap") * 0.12 * fade, t0 + beat / 2, 0.8, 1.0)
            elif perc == "pulse":
                if k % 2 == 0:
                    add(drum("boom") * 0.22 * fade, t0, 1, 1)
            t0 += beat
            k += 1
    # bells / ghanta for sacred moods
    if mood in ("devotional", "divine", "auspicious", "dawn"):
        for at in np.arange(0.2, dur - 2, max(8.0, beat * 16)):
            add(bell(base * 8, 4.0, 0.05), float(at), 0.7, 1.0)
    # fade in/out
    fi = np.minimum(1, _t(n) / 1.5)
    fo = np.minimum(1, (dur - _t(n)) / 2.0)
    env = np.clip(fi * fo, 0, 1)
    return np.stack([L * env, R * env], axis=1)


def reverb(x, seconds=2.2, wet=0.22, seed=0):
    n_ir = int(seconds * SR)
    r = np.random.default_rng(seed)
    t = _t(n_ir)
    out = np.zeros_like(x)
    for ch in range(x.shape[1]):
        ir = r.standard_normal(n_ir).astype(np.float32) * np.exp(-t * 6.9 / seconds)
        ir[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        N = len(x) + n_ir
        nfft = 1 << (N - 1).bit_length()
        y = np.fft.irfft(np.fft.rfft(x[:, ch], nfft) * np.fft.rfft(ir, nfft), nfft)[: len(x)]
        out[:, ch] = x[:, ch] * (1 - wet) + y.astype(np.float32) * wet * 1.6
    return out


def render_music(sections, total, out_wav, base_note="C#", seed=7, log=print):
    notes = {"C": 130.81, "C#": 138.59, "D": 146.83, "D#": 155.56, "E": 164.81, "F": 174.61, "G": 98.0, "A": 110.0, "B": 123.47}
    base = notes.get(base_note, 138.59)
    n = int(total * SR) + SR
    mix = np.zeros((n, 2), np.float32)
    secs = sorted(sections, key=lambda s: s["at"])
    for i, s in enumerate(secs):
        start = float(s["at"])
        end = float(secs[i + 1]["at"]) + 2.0 if i + 1 < len(secs) else total + 1.0
        dur = max(2.0, end - start)
        log(f"[music] section {i + 1}: {s.get('mood')} ({s.get('raga') or MOODS.get(s.get('mood'), MOODS['devotional'])[0]}) "
            f"{start:.1f}s → {end:.1f}s")
        a = section_audio(s.get("mood") or "devotional", s.get("raga"), dur, base, seed + i)
        st = int(start * SR)
        e = min(n, st + len(a))
        mix[st:e] += a[: e - st]
    mix = reverb(mix, 2.6, 0.25)
    peak = np.abs(mix).max() + 1e-9
    mix = mix / peak * 0.7
    write_wav(out_wav, mix)
    return out_wav


def write_wav(path, x, sr=SR):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    y = np.clip(x, -1, 1)
    pcm = (y * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim > 1 else 1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path
