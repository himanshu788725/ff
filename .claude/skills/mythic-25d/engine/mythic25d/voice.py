"""Voice: Hindi TTS with word timings, or align your own recordings.

Engines (storyboard `voice.engine`):
  edge   - Microsoft Edge neural voices via `edge-tts` (free, needs internet).
           Word boundaries come straight from the TTS -> perfect word-timed subs.
  files  - your own recorded lines: shot/line `audio: path.wav`; words are aligned
           with faster-whisper if installed, else an energy-based aligner.
  none   - no audio; timings estimated from the text (for silent previews).

Output: <project>/audio/vo/<shot>_<n>.mp3|wav + <project>/audio/timing.json
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import numpy as np

from .hindi import estimate_duration, weight, words
from .util import ffprobe_duration, load_json, save_json, stable_hash

VOICES = {
    "hi-IN-MadhurNeural": "Hindi male — warm storyteller (default narrator)",
    "hi-IN-SwaraNeural": "Hindi female — clear, gentle",
    "hi-IN-AaravNeural": "Hindi male — young (if available in your region)",
    "hi-IN-AnanyaNeural": "Hindi female — young (if available)",
    "hi-IN-KavyaNeural": "Hindi female (if available)",
    "hi-IN-KunalNeural": "Hindi male (if available)",
    "hi-IN-RehaanNeural": "Hindi male (if available)",
    "en-IN-PrabhatNeural": "Indian English male",
    "en-IN-NeerjaNeural": "Indian English female",
}

# sensible default casting by character category (override per character in storyboard `voices:`)
CAST_VOICE = {
    "female": ("hi-IN-SwaraNeural", "+0%", "+0Hz"),
    "male": ("hi-IN-MadhurNeural", "-4%", "-2Hz"),
    "old": ("hi-IN-MadhurNeural", "-12%", "-8Hz"),
    "child": ("hi-IN-SwaraNeural", "+6%", "+18Hz"),
    "demon": ("hi-IN-MadhurNeural", "-10%", "-22Hz"),
    "divine": ("hi-IN-MadhurNeural", "-10%", "-6Hz"),
}


def voice_for(speaker, board):
    """Resolve (voice, rate, pitch) for a speaker id."""
    vcfg = board.get("voice", {}) or {}
    over = (vcfg.get("cast") or {}).get(speaker) or (board.get("voices") or {}).get(speaker)
    if over:
        if isinstance(over, str):
            return over, vcfg.get("rate", "-6%"), vcfg.get("pitch", "+0Hz")
        return over.get("voice", vcfg.get("narrator", "hi-IN-MadhurNeural")), over.get("rate", "-6%"), over.get("pitch", "+0Hz")
    if speaker in (None, "narrator", "sutradhar"):
        return vcfg.get("narrator", "hi-IN-MadhurNeural"), vcfg.get("rate", "-6%"), vcfg.get("pitch", "-2Hz")
    try:
        from .catalog import get_entity
        e = get_entity(speaker)
    except KeyError:
        e = {}
    if e.get("female"):
        key = "female"
    elif e.get("build") == "child":
        key = "child"
    elif e.get("cat", "").endswith(("rakshasa", "asura")) or e.get("fangs"):
        key = "demon"
    elif e.get("build") == "old" or e.get("beard") == "long":
        key = "old"
    elif e.get("halo"):
        key = "divine"
    else:
        key = "male"
    return CAST_VOICE[key]


# --------------------------------------------------------------------------- utterances

def utterances(board):
    """Flatten storyboard shots into an ordered utterance list."""
    out = []
    for s in board["shots"]:
        k = 0
        if s.get("narration"):
            out.append(dict(shot=s["id"], k=k, speaker="narrator", text=s["narration"].strip(), audio=s.get("narration_audio")))
            k += 1
        for ln in s.get("lines", []) or []:
            out.append(dict(shot=s["id"], k=k, speaker=ln.get("who", "narrator"), text=ln["text"].strip(),
                            audio=ln.get("audio"), gap=ln.get("gap")))
            k += 1
    return out


def _even_word_times(text, dur, start=0.0):
    ws = words(text)
    tot = sum(weight(w) for w in ws) or 1.0
    t = start
    out = []
    for w in ws:
        d = dur * weight(w) / tot
        out.append({"w": w, "s": round(t, 3), "e": round(t + d * 0.92, 3)})
        t += d
    return out


# --------------------------------------------------------------------------- edge-tts

async def _edge_one(text, voice, rate, pitch, out_mp3):
    import edge_tts
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    except TypeError:  # older edge-tts
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    marks = []
    with open(out_mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                marks.append(dict(type=chunk["type"], s=chunk["offset"] / 1e7, d=chunk["duration"] / 1e7, text=chunk["text"]))
    return marks


def _marks_to_words(text, marks, dur):
    """Map TTS word marks onto our display words (punctuation stays attached)."""
    ws = words(text)
    wm = [m for m in marks if m["type"] == "WordBoundary"]
    if not wm:
        sm = [m for m in marks if m["type"] == "SentenceBoundary"]
        if not sm:
            return _even_word_times(text, max(0.3, dur - 0.1))
        out = []
        # distribute words inside each sentence span
        idx = 0
        for m in sm:
            n = len(words(m["text"]))
            seg = " ".join(ws[idx:idx + n])
            out += _even_word_times(seg, m["d"], m["s"])
            idx += n
        if idx < len(ws):
            out += _even_word_times(" ".join(ws[idx:]), 0.6, out[-1]["e"] if out else 0)
        return out
    cores = [w for w in ws if w.strip("।॥,.!?;:—–-\"'“”‘’()… ")]
    if len(cores) != len(wm):
        # TTS split/merged some tokens (numbers, compounds): spread words over the spoken span
        span0, span1 = wm[0]["s"], wm[-1]["s"] + wm[-1]["d"]
        return _even_word_times(text, max(0.3, span1 - span0), span0)
    out = []
    j = 0
    for w in ws:
        if w.strip("।॥,.!?;:—–-\"'“”‘’()… "):
            m = wm[j]
            j += 1
            out.append({"w": w, "s": round(m["s"], 3), "e": round(m["s"] + max(0.12, m["d"]), 3)})
        elif out:
            out[-1]["w"] += " " + w
    # monotonic fix
    for i in range(1, len(out)):
        if out[i]["s"] < out[i - 1]["s"]:
            out[i]["s"] = out[i - 1]["e"]
            out[i]["e"] = max(out[i]["e"], out[i]["s"] + 0.12)
    return out


# --------------------------------------------------------------------------- own recordings: alignment

def _decode_mono(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32), sr


def align_energy(text, audio_path):
    """Dependency-free aligner: find speech span by energy, distribute words by
    syllable weight, then snap internal boundaries to nearby energy dips."""
    x, sr = _decode_mono(audio_path)
    hop = int(sr * 0.01)
    n = max(1, len(x) // hop)
    env = np.sqrt(np.convolve(x[:n * hop].reshape(n, hop).astype(np.float64) ** 2 @ np.ones(hop) / hop,
                              np.ones(5) / 5, mode="same"))
    thr = max(1e-4, np.percentile(env, 30) * 1.8, env.max() * 0.04)
    voiced = np.where(env > thr)[0]
    if len(voiced) == 0:
        return _even_word_times(text, len(x) / sr)
    s0, s1 = voiced[0] * 0.01, voiced[-1] * 0.01 + 0.05
    est = _even_word_times(text, s1 - s0, s0)
    for i in range(1, len(est)):
        b = est[i]["s"]
        lo, hi = int((b - 0.18) / 0.01), int((b + 0.18) / 0.01)
        lo, hi = max(0, lo), min(n - 1, hi)
        if hi > lo:
            dip = lo + int(np.argmin(env[lo:hi]))
            nb = dip * 0.01
            if est[i - 1]["s"] + 0.08 < nb < (est[i + 1]["s"] if i + 1 < len(est) else s1) - 0.08:
                est[i]["s"] = round(nb, 3)
                est[i - 1]["e"] = round(nb - 0.02, 3)
    return est


def align_whisper(text, audio_path):
    """Use faster-whisper word timestamps, mapped onto the known script words."""
    from faster_whisper import WhisperModel  # optional dependency
    model = WhisperModel("small", device="auto", compute_type="int8")
    segs, _ = model.transcribe(str(audio_path), language="hi", word_timestamps=True)
    hw = [w for s in segs for w in (s.words or [])]
    ws = words(text)
    if not hw:
        return align_energy(text, audio_path)
    out = []
    for i, w in enumerate(ws):
        k = min(len(hw) - 1, int(i * len(hw) / max(1, len(ws))))
        out.append({"w": w, "s": round(hw[k].start, 3), "e": round(hw[k].end, 3)})
    return out


# --------------------------------------------------------------------------- main entry

def synthesize(board, proj: Path, log=print, force=False):
    """Produce VO files + timing.json. Returns timing dict."""
    vcfg = board.get("voice", {}) or {}
    engine = vcfg.get("engine", "edge")
    vo_dir = proj / "audio" / "vo"
    vo_dir.mkdir(parents=True, exist_ok=True)
    tpath = proj / "audio" / "timing.json"
    old = load_json(tpath) if tpath.exists() and not force else {}
    old_u = {u["key"]: u for u in old.get("utterances", [])}
    result = []
    edge_ok = engine == "edge"
    if edge_ok:
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            log("[voice] edge-tts not installed -> `pip install edge-tts`. Falling back to estimated timings (silent).")
            edge_ok = False
    for u in utterances(board):
        voice, rate, pitch = voice_for(u["speaker"], board)
        key = stable_hash([u["text"], voice, rate, pitch, engine, u.get("audio")])
        cached = old_u.get(key)
        if cached and cached.get("engine") != "estimate" and (not cached.get("file") or Path(cached["file"]).exists()):
            r = dict(cached, shot=u["shot"], k=u["k"])
            result.append(r)
            continue
        rec = dict(key=key, shot=u["shot"], k=u["k"], speaker=u["speaker"], text=u["text"], voice=voice, rate=rate,
                   pitch=pitch, gap=u.get("gap"))
        if u.get("audio"):
            src = Path(u["audio"])
            if not src.is_absolute():
                src = proj / src
            dur = ffprobe_duration(src)
            try:
                ws = align_whisper(u["text"], src)
                how = "whisper"
            except Exception:
                ws = align_energy(u["text"], src)
                how = "energy"
            rec.update(file=str(src), dur=dur, words=ws, engine=f"file+{how}")
            log(f"[voice] {u['shot']}#{u['k']} own audio aligned ({how}) {dur:.2f}s")
        elif edge_ok:
            out = vo_dir / f"{u['shot']}_{u['k']:02d}.mp3"
            try:
                marks = asyncio.run(_edge_one(u["text"], voice, rate, pitch, str(out)))
                dur = ffprobe_duration(out)
                rec.update(file=str(out), dur=dur, words=_marks_to_words(u["text"], marks, dur), engine="edge")
                log(f"[voice] {u['shot']}#{u['k']} {voice} {dur:.2f}s  {u['text'][:40]}")
            except Exception as ex:
                log(f"[voice] edge-tts failed ({type(ex).__name__}: {str(ex)[:120]}). Using estimated timings "
                    f"(silent) for the rest — check internet / troubleshooting.md, then re-run `voice --force`.")
                edge_ok = False
                try:
                    out.unlink()
                except OSError:
                    pass
                dur = estimate_duration(u["text"])
                rec.update(file=None, dur=dur, words=_even_word_times(u["text"], dur - 0.15), engine="estimate")
        else:
            dur = estimate_duration(u["text"])
            rec.update(file=None, dur=dur, words=_even_word_times(u["text"], dur - 0.15), engine="estimate")
        result.append(rec)
    timing = {"utterances": result}
    save_json(tpath, timing)
    return timing


def load_timing(board, proj: Path):
    tpath = proj / "audio" / "timing.json"
    if tpath.exists():
        t = load_json(tpath)
        keys = {stable_hash([u["text"], *voice_for(u["speaker"], board), (board.get("voice", {}) or {}).get("engine", "edge"),
                             u.get("audio")]) for u in utterances(board)}
        have = {u["key"] for u in t.get("utterances", [])}
        if keys <= have:
            return t
    # estimate without writing audio
    res = []
    for u in utterances(board):
        dur = estimate_duration(u["text"])
        res.append(dict(key="est", shot=u["shot"], k=u["k"], speaker=u["speaker"], text=u["text"], file=None, dur=dur,
                        words=_even_word_times(u["text"], dur - 0.15), engine="estimate", gap=u.get("gap")))
    return {"utterances": res}
