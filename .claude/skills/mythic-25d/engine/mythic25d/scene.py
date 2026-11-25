"""Storyboard (YAML) + voice timing  ->  render plan with absolute times.

Also derives: subtitle events (word-timed), VO cues, SFX cues (explicit + auto
from actions/fx/environment), music sections, intro/outro curtain timing.
"""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

from .catalog import get_entity, register
from .envs import list_envs, parse_env_id
from .actions import ACTIONS
from .hindi import strip_punct

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "4k": (3840, 2160)}

AUTO_ACTION_SFX = {"strike": ("mace_hit", 0.55), "attack": ("mace_hit", 0.55), "fight": ("sword_clash", 0.4),
                   "shoot": ("arrow_whoosh", 0.8), "shoot_arrow": ("arrow_whoosh", 0.8), "throw": ("whoosh", 0.5),
                   "appear": ("divine_shimmer", 0.0), "vanish": ("magic_swell", 0.0), "fly": ("whoosh_long", 0.1),
                   "jump": ("whoosh", 0.1), "fall": ("body_fall", 0.6), "roar": ("roar", 0.0), "rear": ("horse_neigh", 0.1),
                   "grow": ("magic_swell", 0.0), "laugh": ("demon_laugh", 0.0), "bless": ("bell_soft", 0.1),
                   "spin": ("chakra_spin", 0.0), "angry": ("thunder_soft", 0.1), "walk": ("footsteps", 0.0),
                   "run": ("footsteps_fast", 0.0)}
AUTO_FX_SFX = {"lightning": "thunder", "flash": "impact_boom", "divine_burst": "divine_shimmer", "burst": "divine_shimmer",
               "shake": "earthquake", "quake": "earthquake"}
ENV_AMBIENCE = {"forest": "forest_birds", "garden": "forest_birds", "vrindavan": "forest_birds", "ashram": "forest_birds",
                "kurukshetra": "battle_ambience", "war_camp": "campfire", "ocean": "ocean_waves", "ghats": "river",
                "lotus": "river", "kshirsagar": "ocean_waves", "lanka": "ocean_waves", "kailash": "wind",
                "mountain": "wind", "cave": "cave_drips", "shmashan": "wind", "yagya": "fire_crackle", "palace": "palace_hum",
                "temple": "temple_bells", "stage": "audience_murmur", "shadow": "crickets", "cosmic": "cosmic_drone",
                "patala": "cave_drips", "village": "village", "plain": "wind", "swarga": "divine_pad", "dwarka": "ocean_waves"}


def load_board(path) -> dict:
    with open(path, encoding="utf-8") as f:
        board = yaml.safe_load(f)
    if not isinstance(board, dict) or "shots" not in board:
        raise ValueError("storyboard must be a mapping with a `shots:` list")
    if board.get("characters"):
        register(board["characters"])
    return board


def validate(board) -> list:
    """Return a list of human-readable problems (empty = OK)."""
    probs = []
    ids = set()
    env_ids = {e[0] for e in list_envs()}
    for i, s in enumerate(board.get("shots", [])):
        sid = s.get("id") or f"#{i + 1}"
        if sid in ids:
            probs.append(f"{sid}: duplicate shot id")
        ids.add(sid)
        env = s.get("env")
        if not env:
            probs.append(f"{sid}: missing env")
        else:
            try:
                parse_env_id(env)
            except KeyError:
                close = [e for e in env_ids if env.split("_")[0] in e][:5]
                probs.append(f"{sid}: unknown env '{env}' (close: {', '.join(close)})")
        cast_ids = set()
        for c in s.get("cast", []) or []:
            who = c.get("who", c.get("id"))
            try:
                get_entity(who)
            except KeyError as ex:
                probs.append(f"{sid}: {ex}")
            cast_ids.add(c.get("id", who if isinstance(who, str) else None))
            for a in c.get("actions", []) or []:
                if a.get("do") not in ACTIONS:
                    probs.append(f"{sid}: unknown action '{a.get('do')}' for {who}")
            x = c.get("x", 0.5)
            if not (-0.6 <= float(x) <= 1.6):
                probs.append(f"{sid}: {who} x={x} is far off-stage")
        for ln in s.get("lines", []) or []:
            if "text" not in ln:
                probs.append(f"{sid}: a line without text")
            w = ln.get("who")
            if w and w != "narrator" and w not in cast_ids:
                probs.append(f"{sid}: speaker '{w}' is not in this shot's cast (talk animation will be skipped)")
        if not s.get("narration") and not s.get("lines") and not s.get("duration"):
            probs.append(f"{sid}: no narration/lines and no duration -> defaults to 3s")
    return probs


def resolution(board, quality="final"):
    fmt = str(board.get("format", "16:9"))
    W, H = FORMATS.get(fmt, FORMATS["16:9"])
    if quality == "preview":
        W, H = W // 2, H // 2
    elif quality == "draft":
        W, H = W // 3 // 2 * 2, H // 3 // 2 * 2
    return W, H


def keywords_for(board, shot):
    kws = set(shot.get("highlight", []) or []) | set(board.get("highlight", []) or [])
    for c in shot.get("cast", []) or []:
        try:
            e = get_entity(c.get("who", c.get("id")))
            for part in str(e.get("hi", "")).replace("(", " ").replace(")", " ").split():
                if len(part) >= 2:
                    kws.add(part)
        except KeyError:
            pass
    return sorted(kws, key=len, reverse=True)


def compile_plan(board, timing, quality="final", only_shots=None):
    W, H = resolution(board, quality)
    fps = int(board.get("fps", 30 if quality == "final" else 24))
    utts = {}
    for u in timing["utterances"]:
        utts.setdefault(u["shot"], []).append(u)
    intro = dict(board.get("intro", {}) or {})
    outro = dict(board.get("outro", {}) or {})
    if intro.get("curtain"):
        intro.setdefault("pre", 3.5)
        intro.setdefault("open", 2.4)
    if outro.get("curtain"):
        outro.setdefault("post", 4.0)
        outro.setdefault("close", 2.0)
    T = float(intro.get("pre", 0)) if intro.get("curtain") else 0.0
    shots, subs, vo, sfx, music = [], [], [], [], []
    gmusic = board.get("music", {}) or {}
    if isinstance(gmusic, str):
        gmusic = {"mood": gmusic}
    music.append(dict(at=0.0, mood=gmusic.get("mood", "devotional"), raga=gmusic.get("raga"), file=gmusic.get("file")))
    if intro.get("curtain"):
        sfx.append(dict(name="curtain_swish", at=T, vol=-8))
        sfx.append(dict(name="audience_murmur", at=0.0, vol=-24, dur=T + 1.5))
        sfx.append(dict(name="conch", at=0.4, vol=-10))
    for i, s0 in enumerate(board["shots"]):
        s = copy.deepcopy(s0)
        sid = s.get("id") or f"s{i + 1}"
        s["id"] = sid
        lead = float(s.get("lead", 0.6 if i == 0 else 0.35))
        t = lead
        cast = s.get("cast", []) or []
        by_id = {}
        for c in cast:
            cid = c.get("id", c.get("who") if isinstance(c.get("who"), str) else None)
            c["id"] = cid
            by_id[cid] = c
        kws = keywords_for(board, s)
        prev_spk = None
        for u in utts.get(sid, []):
            gap = u.get("gap")
            if gap is None:
                gap = 0.25 if prev_spk == u["speaker"] else 0.45
            if prev_spk is None:
                gap = 0
            t += gap
            ustart = t
            prev_spk = u["speaker"]
            if u.get("file"):
                vo.append(dict(file=u["file"], at=T + ustart, dur=u["dur"], speaker=u["speaker"]))
            ws = [dict(w=w["w"], s=T + ustart + w["s"], e=T + ustart + w["e"]) for w in u["words"]]
            subs.append(dict(shot=sid, speaker=u["speaker"], words=ws, start=T + ustart, end=T + ustart + u["dur"],
                             keywords=kws, translation=None))
            spk = u["speaker"]
            if spk in by_id and spk != "narrator":
                by_id[spk].setdefault("actions", []).append({"do": "talk", "at": ustart, "dur": max(0.4, u["dur"] - 0.1),
                                                              "_seed": i * 1.7})
            t = ustart + u["dur"]
        need = t + float(s.get("pad", 0.7))
        dur = s.get("duration", "auto")
        if dur in (None, "auto"):
            dur = max(need, 2.5 if utts.get(sid) else 3.0)
        else:
            dur = max(float(dur), need)
        s["dur"] = round(dur, 3)
        s["start"] = T
        s.setdefault("transition", "crossfade" if i > 0 else "cut")
        # sfx: explicit
        for c in s.get("sfx", []) or []:
            c = dict(c) if isinstance(c, dict) else {"name": c}
            c["at"] = T + float(c.get("at", 0))
            sfx.append(c)
        # sfx: auto from actions / fx / environment ambience
        if board.get("auto_sfx", True) and s.get("auto_sfx", True):
            for c in cast:
                for a in c.get("actions", []) or []:
                    m = AUTO_ACTION_SFX.get(a.get("do"))
                    if m and a.get("sfx", True):
                        name, frac = m
                        d = float(a.get("dur", 1.0))
                        cue = dict(name=name, at=T + float(a.get("at", 0)) + frac * d, vol=-14 if name.startswith("foot") else -10,
                                   auto=True)
                        if name.startswith("foot"):
                            cue["dur"] = d
                        sfx.append(cue)
            for f in s.get("fx", []) or []:
                if isinstance(f, str) and "@" in f:
                    n, at = f.split("@", 1)
                    if n in AUTO_FX_SFX:
                        sfx.append(dict(name=AUTO_FX_SFX[n], at=T + float(at), vol=-8, auto=True))
            env = s.get("env", "")
            amb = next((v for k, v in ENV_AMBIENCE.items() if env.startswith(k)), None)
            if env.endswith("_night") and amb in ("forest_birds", "village", None):
                amb = "crickets"
            if env.endswith("_fire"):
                amb = "fire_big"
            if env.endswith("_storm"):
                amb = "rain_storm"
            if amb and s.get("ambience", True) is not False:
                sfx.append(dict(name=s.get("ambience") if isinstance(s.get("ambience"), str) else amb, at=T, dur=dur + 0.6,
                                vol=-22, bed=True, auto=True))
        if s.get("music"):
            m = s["music"] if isinstance(s["music"], dict) else {"mood": s["music"]}
            music.append(dict(at=T, mood=m.get("mood"), raga=m.get("raga"), file=m.get("file")))
        if s.get("shloka"):
            sh = dict(s["shloka"])
            sh["at"] = T + float(sh.get("at", 0.4))
            sh["dur"] = float(sh.get("dur", min(dur - 0.6, 7.0)))
            s["_shloka"] = sh
        shots.append(s)
        T += dur
    total = T + (float(outro.get("post", 0)) if outro.get("curtain") else 0.0)
    if outro.get("curtain"):
        sfx.append(dict(name="curtain_swish", at=T, vol=-8))
        sfx.append(dict(name="conch", at=T + 1.6, vol=-10))
    if only_shots:
        keep = set(only_shots)
        shots = [s for s in shots if s["id"] in keep]
        intro, outro = {}, {}
    plan = dict(W=W, H=H, fps=fps, shots=shots, intro=intro, outro=outro, total=total, title=board.get("title", ""),
                subs=subs, vo=vo, sfx=sfx, music=music, quality=quality, subtitle_cfg=board.get("subtitles", {}) or {},
                format=board.get("format", "16:9"), grade=board.get("grade"))
    if board.get("grade") and board.get("grade") != "auto":
        for s in shots:
            s.setdefault("grade", board["grade"])
    return plan
