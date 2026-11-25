"""First-pass mix + master.

mix:    VO (EQ/compression/room) + music bed (ducked under VO) + SFX & ambience
        beds -> soft limiter -> two-pass EBU R128 loudnorm (default -14 LUFS).
master: graded video + film finish (grain/flicker/sharpen) + burned Hindi
        subtitles (libass) + mixed audio -> final mp4 (and a clean version).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from .grade import ffmpeg_finish_filter
from .music import SR, render_music, write_wav
from .sfx import get_sfx
from .util import FONT_DIR, need_bin, run

VO_CHAIN = ("highpass=f=75,lowpass=f=14000,equalizer=f=220:t=q:w=1.2:g=1.5,equalizer=f=3200:t=q:w=1.5:g=2,"
            "acompressor=threshold=-20dB:ratio=3:attack=6:release=140:makeup=3,"
            "aecho=0.8:0.6:38:0.12")


def _decode(path, chain=None):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)]
    if chain:
        cmd += ["-af", chain]
    cmd += ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def _place(buf, x, at, gain=1.0):
    s = int(at * SR)
    if s >= len(buf) or len(x) == 0:
        return
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s] * gain


def _env(x, win=0.05):
    mono = np.abs(x).mean(axis=1)
    k = max(1, int(win * SR))
    c = np.convolve(mono, np.ones(k) / k, mode="same")
    return c


def _smooth_gain(target, attack=0.08, release=0.45):
    """One-pole attack/release smoothing on a per-10ms control signal."""
    step = int(SR * 0.01)
    ctl = target[::step]
    out = np.empty_like(ctl)
    a_up = np.exp(-0.01 / attack)
    a_dn = np.exp(-0.01 / release)
    g = ctl[0] if len(ctl) else 0
    for i, v in enumerate(ctl):
        a = a_up if v > g else a_dn
        g = a * g + (1 - a) * v
        out[i] = g
    return np.repeat(out, step)[: len(target)]


def db(x):
    return 10 ** (x / 20.0)


def mix_project(plan, proj: Path, music_cfg=None, lufs=-14.0, duck_db=10.0, log=print):
    need_bin("ffmpeg")
    total = plan["total"] + 0.5
    n = int(total * SR)
    vo = np.zeros((n, 2), np.float32)
    mus = np.zeros((n, 2), np.float32)
    fx = np.zeros((n, 2), np.float32)
    beds = np.zeros((n, 2), np.float32)
    sfx_dirs = [proj / "sfx"]
    # ---- VO
    for c in plan["vo"]:
        try:
            x = _decode(c["file"], VO_CHAIN)
            _place(vo, x, c["at"], 1.0)
        except Exception as ex:
            log(f"[mix] VO decode failed {c['file']}: {ex}")
    # ---- music
    music_cfg = music_cfg or {}
    mfile = next((m.get("file") for m in plan["music"] if m.get("file")), None) or music_cfg.get("file")
    mvol = float(music_cfg.get("volume_db", -17))
    if music_cfg.get("enabled", True) is not False:
        if mfile:
            mp = Path(mfile)
            if not mp.is_absolute():
                mp = proj / mp
            x = _decode(mp)
            if len(x) < n:
                x = np.tile(x, (int(np.ceil(n / len(x))), 1))
            x = x[:n].copy()
            log(f"[mix] music file: {mp.name}")
        else:
            mw = proj / "audio" / "music.wav"
            render_music(plan["music"], total, mw, base_note=music_cfg.get("key", "C#"), log=log)
            x = _decode(mw)[:n]
        t = np.arange(len(x)) / SR
        fade = np.clip(t / 1.5, 0, 1) * np.clip((total - t) / 3.0, 0, 1)
        _place(mus, x * fade[:, None], 0, db(mvol))
    # ---- sfx & beds
    for c in plan["sfx"]:
        try:
            d = c.get("dur")
            x = get_sfx(c["name"], d, extra_dirs=sfx_dirs)
            if d and len(x) > int(d * SR):
                x = x[: int(d * SR)]
            if c.get("bed") or (d and d > 3):
                L = len(x)
                ramp = min(int(1.2 * SR), L // 3)
                if ramp > 0:
                    w = np.linspace(0, 1, ramp)[:, None]
                    x = x.copy()
                    x[:ramp] *= w
                    x[-ramp:] *= w[::-1]
            target = beds if c.get("bed") else fx
            _place(target, x, float(c["at"]), db(float(c.get("vol", -10))))
        except KeyError as ex:
            log(f"[mix] {ex}")
    # ---- ducking (music & beds under VO)
    if np.abs(vo).max() > 1e-4:
        e = _env(vo, 0.06)
        e = e / (e.max() + 1e-9)
        tgt = np.clip(e * 4.0, 0, 1)
        g = _smooth_gain(tgt)
        g = g[:n]
        if len(g) < n:
            g = np.pad(g, (0, n - len(g)))
        mus *= (1 - (1 - db(-duck_db)) * g)[:, None]
        beds *= (1 - (1 - db(-duck_db * 0.6)) * g)[:, None]
    out = vo + mus + fx + beds
    # soft limiter
    pk = np.abs(out).max() + 1e-9
    if pk > 0.95:
        out = np.tanh(out / pk * 1.4) / np.tanh(1.4) * 0.95
    raw = proj / "audio" / "mix_raw.wav"
    write_wav(raw, out)
    final = proj / "audio" / "mix.wav"
    loudnorm(raw, final, lufs, log=log)
    # stems for re-mixing in a DAW
    stems = proj / "audio" / "stems"
    for name, arr in (("vo", vo), ("music", mus), ("sfx", fx), ("ambience", beds)):
        write_wav(stems / f"{name}.wav", np.clip(arr, -1, 1))
    log(f"[mix] wrote {final} (+ stems in audio/stems/)")
    return final


def loudnorm(src, dst, lufs=-14.0, tp=-1.5, lra=11, log=print):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                        f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    try:
        js = json.loads(txt[txt.rindex("{"): txt.rindex("}") + 1])
        af = (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    except Exception:
        af = f"loudnorm=I={lufs}:TP={tp}:LRA={lra}"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af, "-ar", "48000", str(dst)])
    return dst


def measure_loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    out = {}
    for key, tag in (("I", "I:"), ("LRA", "LRA:"), ("TP", "Peak:")):
        idx = txt.rfind(tag)
        if idx >= 0:
            try:
                out[key] = float(txt[idx + len(tag):].split()[0])
            except ValueError:
                pass
    return out


def master(video_raw: Path, audio: Path | None, ass: Path | None, out: Path, finish=None, crf=18, preset="slow",
           burn_subs=True, log=print):
    need_bin("ffmpeg")
    finish = finish if finish is not None else ffmpeg_finish_filter()
    vf = []
    if finish:
        vf.append(finish)
    if burn_subs and ass and Path(ass).exists():
        a = str(ass).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        fd = str(FONT_DIR).replace("\\", "/").replace(":", "\\:")
        vf.append(f"ass='{a}':fontsdir='{fd}'")
    vf.append("format=yuv420p")
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-i", str(video_raw)]
    if audio and Path(audio).exists():
        cmd += ["-i", str(audio)]
    # bitrate cap keeps grain from exploding file size (~14 Mbps at 1080p30, scales with pixels)
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0", str(video_raw)], capture_output=True, text=True).stdout.strip().split(",")
    try:
        px = int(pr[0]) * int(pr[1])
    except (ValueError, IndexError):
        px = 1920 * 1080
    mbps = max(3.0, 14.0 * px / (1920 * 1080))
    cmd += ["-vf", ",".join(vf), "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-maxrate", f"{mbps:.1f}M",
            "-bufsize", f"{mbps * 2:.1f}M", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if audio and Path(audio).exists():
        cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    log("[master] " + " ".join(cmd[:4]) + " ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg master failed:\n" + "\n".join(r.stderr.strip().splitlines()[-20:]))
    return out
