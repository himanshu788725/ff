"""mythic.py — command line for the Mythic 2.5D painted-puppet film engine.

  mythic.py doctor                         check ffmpeg / fonts / libass / edge-tts
  mythic.py new <name> [--format 9:16]     create mythic_projects/<name>/ from template
  mythic.py list chars|animals|birds|envs|props|actions|moods|ragas|grades|sfx|voices [--cat X]
  mythic.py search <text>                  find characters/animals by Hindi or English name
  mythic.py char <id> [--out x.png]        pose sheet of one character (stand/talk/bless/namaste/raise/seated)
  mythic.py gallery [--cat devi] [--kind humanoid]  contact sheet of catalog entries
  mythic.py env <env_id> [--out x.jpg]     preview an environment
  mythic.py validate <proj>
  mythic.py voice <proj> [--force]         TTS (edge-tts) or align own recordings -> audio/timing.json
  mythic.py still <proj> --t 12.5 | --shot s3 [--quality preview]
  mythic.py render <proj> [--quality preview|final|draft] [--shots s1,s2] [--workers N]
  mythic.py subs <proj>                    write subs/subs.ass + subs.srt
  mythic.py music <proj>                   render the procedural score only
  mythic.py mix <proj> [--lufs -14]
  mythic.py master <proj> [--no-burn]
  mythic.py review <proj>
  mythic.py make <proj> [--quality preview|final]   everything above in order
  mythic.py lut <grade|all> [--out dir]    export .cube LUTs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .util import FONT_DIR, PKG_DIR, fmt_time

TEMPLATES = PKG_DIR.parent.parent / "templates"


def proj_path(name) -> Path:
    p = Path(name)
    if p.exists():
        return p.resolve()
    q = Path("mythic_projects") / name
    if q.exists():
        return q.resolve()
    raise SystemExit(f"project '{name}' not found (looked at ./{name} and ./mythic_projects/{name})")


def board_of(proj: Path):
    from .scene import load_board
    sb = proj / "storyboard.yaml"
    if not sb.exists():
        raise SystemExit(f"{sb} missing")
    return load_board(sb)


def plan_of(proj, quality="final", only=None):
    from .scene import compile_plan
    from .voice import load_timing
    board = board_of(proj)
    timing = load_timing(board, proj)
    return board, compile_plan(board, timing, quality, only)


# --------------------------------------------------------------------------- commands

def cmd_doctor(a):
    ok = True

    def line(flag, msg):
        print(("  ✔ " if flag else "  ✘ ") + msg)

    for b in ("ffmpeg", "ffprobe"):
        p = shutil.which(b)
        line(bool(p), f"{b}: {p or 'NOT FOUND — install ffmpeg (see troubleshooting.md)'}")
        ok &= bool(p)
    if shutil.which("ffmpeg"):
        f = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        has_ass = bool(re.search(r"\bass\s+V->V", f))
        line(has_ass, "ffmpeg libass (Hindi subtitle burn-in)" + ("" if has_ass else " — MISSING: use a full ffmpeg build"))
        b = subprocess.run(["ffmpeg", "-hide_banner", "-buildconf"], capture_output=True, text=True).stdout
        line("libharfbuzz" in b, "ffmpeg built with HarfBuzz (correct Devanagari shaping)" + ("" if "libharfbuzz" in b else
                                                                                               " — matras may render wrong"))
    fonts = sorted(p.name for p in FONT_DIR.glob("*.ttf"))
    line(any("Tiro" in x for x in fonts), f"fonts: {', '.join(fonts)}")
    try:
        from PIL import features
        line(True, f"Pillow raqm (complex text in previews): {features.check('raqm')}")
    except Exception:
        pass
    try:
        import numpy, yaml  # noqa
        line(True, "numpy + pyyaml")
    except ImportError as ex:
        line(False, f"python deps: {ex} — pip install -r requirements.txt")
        ok = False
    try:
        import edge_tts  # noqa
        line(True, "edge-tts installed (Hindi neural voices)")
    except ImportError:
        line(False, "edge-tts not installed — pip install edge-tts (or use voice.engine: files/none)")
    try:
        import faster_whisper  # noqa
        line(True, "faster-whisper installed (better alignment of your own recordings)")
    except ImportError:
        print("  · faster-whisper not installed (optional; energy aligner will be used for own recordings)")
    print(f"  · CPU cores: {os.cpu_count()}")
    print("doctor:", "OK" if ok else "problems found")


def cmd_new(a):
    root = Path(a.dir or "mythic_projects") / a.name
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"{root} already exists")
    root.mkdir(parents=True, exist_ok=True)
    tpl = TEMPLATES / ("storyboard_shorts.yaml" if a.format == "9:16" else "storyboard_template.yaml")
    txt = tpl.read_text(encoding="utf-8").replace("__TITLE__", a.title or a.name)
    (root / "storyboard.yaml").write_text(txt, encoding="utf-8")
    (root / "script.txt").write_text("# अपनी हिंदी कहानी/स्क्रिप्ट यहाँ लिखें (Claude इसे storyboard.yaml में बदल देगा)\n", encoding="utf-8")
    (root / "sfx").mkdir(exist_ok=True)
    (root / "sfx" / "README.txt").write_text("Drop real SFX here named like the cue (e.g. horse_neigh.wav, conch.mp3) "
                                             "to replace the synthetic ones.\n", encoding="utf-8")
    print(f"created {root}  — edit storyboard.yaml, then: mythic.py make {root} --quality preview")


def cmd_list(a):
    what = a.what
    if what in ("chars", "characters", "animals", "birds", "all"):
        from .catalog import all_entities
        kinds = {"chars": ("humanoid",), "characters": ("humanoid",), "animals": ("quadruped", "serpent", "fish"),
                 "birds": ("bird",), "all": ("humanoid", "quadruped", "serpent", "fish", "bird")}[what]
        es = [e for e in all_entities().values() if e.get("kind", "humanoid") in kinds and (not a.cat or a.cat in e.get("cat", ""))]
        cats = {}
        for e in es:
            cats.setdefault(e.get("cat", "?"), []).append(e)
        for c, lst in cats.items():
            print(f"\n## {c} ({len(lst)})")
            for e in lst:
                print(f"  {e['id']:<26} {e.get('hi', ''):<22} {e.get('en', '')}")
        print(f"\n{len(es)} entries")
    elif what == "envs":
        from .envs import list_envs
        for eid, desc, t in list_envs():
            print(f"  {eid:<28} {desc}  [{t}]")
        print(f"\n{len(list_envs())} environments")
    elif what == "props":
        from .props import PROPS, HANGING
        for k in PROPS:
            print(f"  {k}{'  (hangs on strings)' if k in HANGING else ''}")
    elif what == "actions":
        from .actions import ACTION_HELP
        for k, v in ACTION_HELP.items():
            print(f"  {k:<12} {v}")
    elif what in ("moods", "ragas"):
        from .music import MOODS, RAGAS
        if what == "moods":
            for k, v in MOODS.items():
                print(f"  {k:<12} raga={v[0]:<12} {v[1]}bpm lead={v[2]:<8} perc={v[3]}")
        else:
            for k, v in RAGAS.items():
                print(f"  {k:<16} notes={v[0]}")
    elif what == "grades":
        from .grade import GRADES
        for k, v in GRADES.items():
            print(f"  {k:<13} {v['desc']}")
    elif what == "sfx":
        from .sfx import GEN
        print("  " + "\n  ".join(sorted(GEN)))
    elif what == "voices":
        from .voice import VOICES
        for k, v in VOICES.items():
            print(f"  {k:<22} {v}")
    elif what == "cameras":
        from .render import CAM_PRESETS
        print("  " + "\n  ".join(CAM_PRESETS))
    else:
        raise SystemExit("list what? chars|animals|birds|all|envs|props|actions|moods|ragas|grades|sfx|voices|cameras")


def cmd_search(a):
    from .catalog import search
    for e in search(a.query):
        print(f"  {e['id']:<26} {e.get('kind', ''):<10} {e.get('hi', ''):<22} {e.get('en', '')}")


def _pose_sheet(ids, out, W=None, poses=None, label=True):
    from PIL import Image, ImageDraw
    from .render import Timeline
    poses = poses or [("stand", []), ("talk", [{"do": "talk", "at": 0, "dur": 9}]), ("bless", [{"do": "bless", "at": 0, "dur": 9}]),
                      ("namaste", [{"do": "namaste", "at": 0, "dur": 9}]), ("raise", [{"do": "raise", "at": 0, "dur": 9}]),
                      ("seated", [{"do": "sit", "at": 0}])]
    tiles = []
    for who in ids:
        for pname, acts in poses:
            plan = {"W": 400, "H": 400, "fps": 24, "shots": [{"id": "x", "env": "plain_day", "dur": 3, "grade": "kathaa",
                                                              "camera": {"move": "static", "from": 1.0, "to": 1.0, "y": [0.36, 0.36]},
                                                              "cast": [{"who": who, "x": 0.5, "actions": acts, "strings": False,
                                                                        "scale": 1.35}],
                                                              "fx": ["no_particles"], "light": {"vignette": 0.35, "rays": 0}}]}
            img = Timeline(plan).render(24)
            if label:
                d = ImageDraw.Draw(img)
                d.text((8, 8), f"{who} · {pname}" if len(poses) > 1 else str(who), fill=(242, 201, 74))
            tiles.append(img)
    cols = len(poses) if len(ids) > 1 or len(poses) > 1 else 1
    cols = min(cols, 8) if len(poses) > 1 else 8
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (400 * cols, 400 * rows), (20, 14, 10))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 400, (i // cols) * 400))
    sheet.save(out, quality=88)
    print(f"wrote {out}")


def cmd_char(a):
    _pose_sheet([a.id], a.out or f"{a.id}_poses.jpg")


def cmd_gallery(a):
    from .catalog import all_entities
    es = [e for e in all_entities().values() if (not a.cat or a.cat in e.get("cat", "")) and
          (not a.kind or e.get("kind", "humanoid") == a.kind)]
    es = es[a.offset:a.offset + a.limit]
    from PIL import Image, ImageDraw
    from .render import Timeline
    tiles = []
    for e in es:
        kind = e.get("kind", "humanoid")
        sc = {"humanoid": 1.12, "quadruped": 0.85, "bird": 1.1}.get(kind, 1.0)
        plan = {"W": 320, "H": 320, "fps": 24, "shots": [{"id": "x", "env": "plain_day", "dur": 3, "grade": "kathaa",
                                                          "camera": {"move": "static", "from": 1.0, "to": 1.0, "y": [0.36, 0.36]},
                                                          "cast": [{"who": e["id"], "x": 0.5, "strings": False, "scale": sc}],
                                                          "fx": ["no_particles"], "light": {"vignette": 0.35, "rays": 0}}]}
        try:
            img = Timeline(plan).render(10)
        except Exception as ex:
            img = Image.new("RGB", (320, 320), (60, 20, 20))
            print(f"  ! {e['id']}: {ex}")
        ImageDraw.Draw(img).text((6, 6), e["id"], fill=(242, 201, 74))
        tiles.append(img)
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (320 * cols, 320 * max(1, rows)), (20, 14, 10))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 320, (i // cols) * 320))
    out = a.out or f"gallery_{a.cat or a.kind or 'all'}_{a.offset}.jpg"
    sheet.save(out, quality=86)
    print(f"wrote {out} ({len(tiles)} entries)")


def cmd_env(a):
    from .render import Timeline
    W, H = (960, 540) if a.format != "9:16" else (540, 960)
    plan = {"W": W, "H": H, "fps": 24, "shots": [{"id": "x", "env": a.env_id, "dur": 4, "camera": {"move": "static"},
                                                  "cast": []}]}
    img = Timeline(plan).render(24)
    out = a.out or f"{a.env_id}.jpg"
    img.save(out, quality=90)
    print(f"wrote {out}")


def cmd_validate(a):
    from .scene import validate
    proj = proj_path(a.proj)
    board = board_of(proj)
    probs = validate(board)
    if probs:
        print("\n".join("  ✘ " + p for p in probs))
        print(f"{len(probs)} problem(s)")
        if any("unknown" in p for p in probs):
            sys.exit(1)
    else:
        print(f"  ✔ storyboard OK ({len(board['shots'])} shots)")


def cmd_voice(a):
    from .voice import synthesize
    proj = proj_path(a.proj)
    board = board_of(proj)
    t = synthesize(board, proj, force=a.force)
    tot = sum(u["dur"] for u in t["utterances"])
    engines = {u["engine"] for u in t["utterances"]}
    print(f"[voice] {len(t['utterances'])} utterances, {tot:.1f}s of speech, engines={engines}")


def cmd_subs(a):
    from .subs import build_ass, build_srt
    proj = proj_path(a.proj)
    board, plan = plan_of(proj, a.quality)
    build_ass(plan, proj / "subs" / f"subs_{plan['W']}x{plan['H']}.ass")
    build_srt(plan, proj / "subs" / "subs.srt")
    print(f"[subs] wrote {proj / 'subs'}")


def cmd_still(a):
    from .render import Timeline
    proj = proj_path(a.proj)
    board, plan = plan_of(proj, a.quality)
    t = a.t
    if a.shot:
        s = next(s for s in plan["shots"] if s["id"] == a.shot)
        t = s["start"] + s["dur"] * 0.5
    tl = Timeline(plan)
    img = tl.render(int((t or 0) * plan["fps"]))
    out = Path(a.out or proj / "review" / f"still_{(t or 0):.2f}.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=92)
    print(f"wrote {out}")


def cmd_render(a):
    from .render import render_video
    proj = proj_path(a.proj)
    only = a.shots.split(",") if a.shots else None
    board, plan = plan_of(proj, a.quality, only)
    out = proj / "build" / f"video_{a.quality}{'_' + '_'.join(only) if only else ''}.mp4"
    render_video(plan, out, workers=a.workers, crf=16 if a.quality == "final" else 22,
                 preset="veryfast" if a.quality != "final" else "fast")
    return out


def cmd_music(a):
    from .music import render_music
    proj = proj_path(a.proj)
    board, plan = plan_of(proj)
    render_music(plan["music"], plan["total"] + 0.5, proj / "audio" / "music.wav")


def cmd_mix(a):
    from .mix import mix_project
    proj = proj_path(a.proj)
    board, plan = plan_of(proj)
    mc = board.get("music", {}) or {}
    if isinstance(mc, str):
        mc = {"mood": mc}
    mix_project(plan, proj, mc, lufs=a.lufs)


def cmd_master(a):
    from .mix import master
    from .subs import build_ass, build_srt
    proj = proj_path(a.proj)
    board, plan = plan_of(proj, a.quality)
    raw = proj / "build" / f"video_{a.quality}.mp4"
    if not raw.exists():
        raise SystemExit(f"{raw} not found — run render first")
    ass = build_ass(plan, proj / "subs" / f"subs_{plan['W']}x{plan['H']}.ass")
    build_srt(plan, proj / "subs" / "subs.srt")
    audio = proj / "audio" / "mix.wav"
    name = re.sub(r"[^\w\-]+", "_", proj.name)
    out = proj / "out" / f"{name}_{a.quality}.mp4"
    master(raw, audio if audio.exists() else None, ass, out, burn_subs=not a.no_burn,
           preset="medium" if a.quality == "final" else "veryfast", crf=19 if a.quality == "final" else 23)
    if a.quality == "final" and not a.no_burn:
        master(raw, audio if audio.exists() else None, None, proj / "out" / f"{name}_clean.mp4", burn_subs=False,
               preset="medium", crf=19)
    print(f"[master] wrote {out}")
    return out


def cmd_review(a):
    from .review import review_project
    proj = proj_path(a.proj)
    board, plan = plan_of(proj, a.quality)
    name = re.sub(r"[^\w\-]+", "_", proj.name)
    video = proj / "out" / f"{name}_{a.quality}.mp4"
    if not video.exists():
        video = proj / "build" / f"video_{a.quality}.mp4"
    review_project(proj, plan, video if video.exists() else None, proj / "audio" / "mix.wav")


def cmd_make(a):
    t0 = time.time()
    proj = proj_path(a.proj)
    cmd_validate(argparse.Namespace(proj=a.proj))
    if not a.skip_voice:
        cmd_voice(argparse.Namespace(proj=a.proj, force=False))
    cmd_render(argparse.Namespace(proj=a.proj, quality=a.quality, shots=None, workers=a.workers))
    cmd_mix(argparse.Namespace(proj=a.proj, lufs=a.lufs))
    cmd_master(argparse.Namespace(proj=a.proj, quality=a.quality, no_burn=False))
    cmd_review(argparse.Namespace(proj=a.proj, quality=a.quality))
    print(f"[make] done in {fmt_time(time.time() - t0)}")


def cmd_lut(a):
    from .grade import GRADES, write_cube
    out = Path(a.out or "luts")
    out.mkdir(parents=True, exist_ok=True)
    names = list(GRADES) if a.grade == "all" else [a.grade]
    for n in names:
        print("wrote", write_cube(n, out / f"mythic_{n}.cube"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mythic.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sp.add_parser("new")
    p.add_argument("name")
    p.add_argument("--format", default="16:9")
    p.add_argument("--title")
    p.add_argument("--dir")
    p.set_defaults(fn=cmd_new)
    p = sp.add_parser("list")
    p.add_argument("what")
    p.add_argument("--cat")
    p.set_defaults(fn=cmd_list)
    p = sp.add_parser("search")
    p.add_argument("query")
    p.set_defaults(fn=cmd_search)
    p = sp.add_parser("char")
    p.add_argument("id")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_char)
    p = sp.add_parser("gallery")
    p.add_argument("--cat")
    p.add_argument("--kind")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=64)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_gallery)
    p = sp.add_parser("env")
    p.add_argument("env_id")
    p.add_argument("--out")
    p.add_argument("--format", default="16:9")
    p.set_defaults(fn=cmd_env)
    for name, fn in (("validate", cmd_validate), ("music", cmd_music)):
        p = sp.add_parser(name)
        p.add_argument("proj")
        p.set_defaults(fn=fn)
    p = sp.add_parser("voice")
    p.add_argument("proj")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_voice)
    for name, fn in (("subs", cmd_subs), ("review", cmd_review)):
        p = sp.add_parser(name)
        p.add_argument("proj")
        p.add_argument("--quality", default="final")
        p.set_defaults(fn=fn)
    p = sp.add_parser("still")
    p.add_argument("proj")
    p.add_argument("--t", type=float)
    p.add_argument("--shot")
    p.add_argument("--quality", default="final")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_still)
    p = sp.add_parser("render")
    p.add_argument("proj")
    p.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    p.add_argument("--shots")
    p.add_argument("--workers", type=int)
    p.set_defaults(fn=cmd_render)
    p = sp.add_parser("mix")
    p.add_argument("proj")
    p.add_argument("--lufs", type=float, default=-14.0)
    p.set_defaults(fn=cmd_mix)
    p = sp.add_parser("master")
    p.add_argument("proj")
    p.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    p.add_argument("--no-burn", action="store_true")
    p.set_defaults(fn=cmd_master)
    p = sp.add_parser("make")
    p.add_argument("proj")
    p.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    p.add_argument("--workers", type=int)
    p.add_argument("--lufs", type=float, default=-14.0)
    p.add_argument("--skip-voice", action="store_true")
    p.set_defaults(fn=cmd_make)
    p = sp.add_parser("lut")
    p.add_argument("grade")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_lut)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
