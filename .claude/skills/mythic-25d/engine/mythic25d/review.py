"""Review helper: QA checks + an HTML review page with per-shot thumbnails.

`review_project(proj, plan, video)` writes review/index.html, review/qa.json,
review/contact_sheet.jpg and returns the QA dict (also printed as text so an
agent can act on it).
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

from .hindi import split_lines
from .mix import measure_loudness
from .util import FONT_DIR, ffprobe_duration, fmt_time


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate",
                        "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def _detect(path, vf):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", vf, "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    return r.stderr


def _thumb(video, t, out, width=480):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", f"scale={width}:-2", "-q:v", "3", str(out)], check=False)
    return out


def subtitle_checks(plan, lufs_target=-14.0):
    issues = []
    rows = []
    portrait = plan["H"] > plan["W"]
    max_chars = 22 if portrait else 38
    for sub in plan["subs"]:
        for ln in split_lines(sub["words"], max_chars, 4 if portrait else 7):
            text = " ".join(w["w"] for w in ln)
            dur = ln[-1]["e"] - ln[0]["s"] + 0.3
            chars = len(text.replace(" ", ""))
            cps = chars / max(0.1, dur)
            flag = []
            if cps > 20:
                flag.append(f"fast {cps:.0f} cps")
            if dur < 0.8:
                flag.append(f"short {dur:.2f}s")
            if len(text) > max_chars + 6:
                flag.append(f"long {len(text)} chars")
            rows.append(dict(shot=sub["shot"], start=ln[0]["s"], end=ln[-1]["e"], text=text, cps=round(cps, 1), flags=flag))
            if flag:
                issues.append(f"subs {sub['shot']} @{fmt_time(ln[0]['s'])}: {', '.join(flag)} — “{text}”")
    return rows, issues


def review_project(proj: Path, plan: dict, video: Path | None, audio: Path | None = None, lufs_target=-14.0, log=print):
    rv = proj / "review"
    (rv / "thumbs").mkdir(parents=True, exist_ok=True)
    qa = {"errors": [], "warnings": [], "info": {}}
    W, H = plan["W"], plan["H"]
    # ---------------- fonts / libass
    fonts = sorted(p.name for p in FONT_DIR.glob("*.ttf"))
    if not any("Devanagari" in f or "Tiro" in f for f in fonts):
        qa["errors"].append("No Devanagari font in engine fonts/ — subtitles will show boxes.")
    filt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    if not re.search(r"\bass\s+V->V", filt):
        qa["errors"].append("ffmpeg has no libass (ass filter) — cannot burn subtitles. See troubleshooting.md")
    # ---------------- timing / voice
    est = [u for u in plan.get("vo", [])]
    if not est:
        qa["warnings"].append("No voice-over audio in the mix (engine=none or edge-tts unavailable). Timings are estimated.")
    for s in plan["shots"]:
        if s["dur"] < 1.5:
            qa["warnings"].append(f"shot {s['id']} is very short ({s['dur']:.2f}s)")
        if s["dur"] > 25:
            qa["warnings"].append(f"shot {s['id']} is long ({s['dur']:.1f}s) — consider splitting for pacing / camera variety")
        if not s.get("cast"):
            qa["warnings"].append(f"shot {s['id']} has no cast (pure establishing shot) — fine if intended")
    rows, sub_issues = subtitle_checks(plan, lufs_target)
    qa["warnings"] += sub_issues[:40]
    if len(sub_issues) > 40:
        qa["warnings"].append(f"... {len(sub_issues) - 40} more subtitle warnings")
    # ---------------- video
    thumbs = []
    if video and Path(video).exists():
        pr = _probe(video)
        dur = float(pr.get("format", {}).get("duration", 0) or 0)
        vs = [s for s in pr.get("streams", []) if s.get("codec_type") == "video"]
        aus = [s for s in pr.get("streams", []) if s.get("codec_type") == "audio"]
        qa["info"]["video"] = dict(duration=round(dur, 2), size=f"{vs[0]['width']}x{vs[0]['height']}" if vs else "?",
                                   fps=vs[0].get("r_frame_rate") if vs else "?", audio=bool(aus))
        if abs(dur - plan["total"]) > 0.6:
            qa["warnings"].append(f"video duration {dur:.2f}s differs from plan {plan['total']:.2f}s")
        if not aus:
            qa["warnings"].append("final video has no audio stream")
        bd = _detect(video, "blackdetect=d=0.6:pix_th=0.06")
        blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
        for a, b in blacks:
            a, b = float(a), float(b)
            if a > 0.5 and b < dur - 0.5:
                qa["warnings"].append(f"black frames {fmt_time(a)}–{fmt_time(b)}")
        fz = _detect(video, "freezedetect=n=0.0008:d=3")
        for a, b in re.findall(r"freeze_start: ([\d.]+).*?freeze_end: ([\d.]+)", fz, re.S):
            qa["warnings"].append(f"near-static picture {fmt_time(float(a))}–{fmt_time(float(b))} (puppets idle? add an action/camera move)")
        for s in plan["shots"]:
            tt = [s["start"] + 0.35, s["start"] + s["dur"] / 2, s["start"] + s["dur"] - 0.35]
            ims = []
            for k, t in enumerate(tt):
                p = rv / "thumbs" / f"{s['id']}_{k}.jpg"
                _thumb(video, t, p)
                ims.append(p)
            thumbs.append((s, ims))
        # contact sheet
        try:
            tiles = [Image.open(p) for _, ims in thumbs for p in ims[1:2] if p.exists()]
            if tiles:
                tw, th = tiles[0].size
                cols = 4
                rows_n = (len(tiles) + cols - 1) // cols
                sheet = Image.new("RGB", (tw * cols, th * rows_n), (20, 14, 10))
                for i, im in enumerate(tiles):
                    sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
                sheet.save(rv / "contact_sheet.jpg", quality=88)
        except Exception as ex:
            qa["warnings"].append(f"contact sheet failed: {ex}")
    else:
        qa["warnings"].append("no rendered video found — run render/master first")
    # ---------------- audio
    if audio and Path(audio).exists():
        L = measure_loudness(audio)
        qa["info"]["audio"] = L
        if "I" in L and abs(L["I"] - lufs_target) > 1.5:
            qa["warnings"].append(f"integrated loudness {L['I']} LUFS (target {lufs_target})")
        if "TP" in L and L["TP"] > -0.5:
            qa["warnings"].append(f"true peak {L['TP']} dBFS — risk of clipping after encoding")
    qa["info"]["shots"] = len(plan["shots"])
    qa["info"]["total"] = round(plan["total"], 2)
    qa["info"]["subtitle_lines"] = len(rows)
    (rv / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_html(rv / "index.html", proj, plan, qa, thumbs, rows, video)
    # text summary
    log(f"[review] {proj.name}: {qa['info'].get('shots')} shots, {qa['info'].get('total')}s, "
        f"{len(qa['errors'])} errors, {len(qa['warnings'])} warnings")
    for e in qa["errors"]:
        log("  ERROR  " + e)
    for w in qa["warnings"][:25]:
        log("  warn   " + w)
    log(f"[review] open {rv / 'index.html'}")
    return qa


def _write_html(path, proj, plan, qa, thumbs, rows, video):
    e = html.escape
    rel_video = ""
    if video:
        try:
            rel_video = str(Path(video).resolve().relative_to(path.parent.parent.resolve()))
            rel_video = "../" + rel_video
        except ValueError:
            rel_video = str(video)
    shot_html = []
    for s, ims in thumbs:
        cast = ", ".join(str(c.get("who", c.get("id"))) for c in s.get("cast", []) or [])
        imgs = "".join(f'<img src="thumbs/{p.name}" loading="lazy">' for p in ims)
        shot_html.append(f"""<div class="shot"><div class="imgs">{imgs}</div><div class="meta">
<b>{e(s['id'])}</b> · {fmt_time(s['start'])} · {s['dur']:.1f}s · <code>{e(s['env'])}</code> · cam <code>{e(str((s.get('camera') or {}).get('move', 'drift')))}</code><br>
<span class="cast">{e(cast)}</span><p lang="hi">{e(s.get('narration', '') or '')}</p></div></div>""")
    sub_rows = "".join(
        f"<tr class='{'bad' if r['flags'] else ''}'><td>{e(r['shot'])}</td><td>{fmt_time(r['start'])}</td><td lang='hi'>{e(r['text'])}</td>"
        f"<td>{r['cps']}</td><td>{e(', '.join(r['flags']))}</td></tr>" for r in rows)
    errs = "".join(f"<li class='err'>{e(x)}</li>" for x in qa["errors"]) or "<li class='ok'>No errors</li>"
    warns = "".join(f"<li class='warn'>{e(x)}</li>" for x in qa["warnings"]) or "<li class='ok'>No warnings</li>"
    info = qa["info"]
    a = info.get("audio", {})
    v = info.get("video", {})
    page = f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review — {e(proj.name)}</title><style>
:root{{--bg:#16100c;--fg:#f1e2bf;--mut:#b9a98a;--acc:#f2c94a;--bad:#e0765a;--ok:#9fd8c2;--card:#22180f}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,'Noto Sans Devanagari',sans-serif;margin:0;padding:24px 16px;max-width:1200px;margin:auto}}
h1{{color:var(--acc);font-weight:600;margin:0 0 4px}} h2{{margin-top:32px;border-bottom:1px solid #3a2a1c;padding-bottom:4px}}
.stats{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}} .stat{{background:var(--card);padding:10px 14px;border-radius:8px;min-width:120px}}
.stat b{{display:block;font-size:20px;color:var(--acc)}} li.err{{color:var(--bad)}} li.warn{{color:#f0c890}} li.ok{{color:var(--ok)}}
.shot{{display:flex;gap:12px;background:var(--card);border-radius:8px;padding:10px;margin:10px 0;flex-wrap:wrap}}
.imgs{{display:flex;gap:6px;flex-wrap:wrap}} .imgs img{{width:220px;max-width:100%;border-radius:4px}} .meta{{flex:1;min-width:240px}}
.cast{{color:var(--mut)}} code{{color:var(--ok)}} table{{border-collapse:collapse;width:100%;font-size:14px}}
td,th{{border-bottom:1px solid #3a2a1c;padding:4px 6px;text-align:left;vertical-align:top}} tr.bad td{{color:var(--bad)}}
video{{width:100%;max-height:70vh;background:#000;border-radius:8px}} .wrap{{overflow-x:auto}}
</style></head><body>
<h1>{e(plan.get('title') or proj.name)}</h1><div class="cast">mythic25d review · {e(plan.get('format', '16:9'))} · {plan['W']}x{plan['H']} @ {plan['fps']}fps</div>
<div class="stats"><div class="stat"><b>{info.get('total')}s</b>duration</div><div class="stat"><b>{info.get('shots')}</b>shots</div>
<div class="stat"><b>{info.get('subtitle_lines')}</b>subtitle lines</div><div class="stat"><b>{a.get('I', '—')}</b>LUFS</div>
<div class="stat"><b>{a.get('TP', '—')}</b>true peak dBFS</div><div class="stat"><b>{len(qa['errors'])}/{len(qa['warnings'])}</b>errors/warnings</div></div>
{f'<video controls src="{e(rel_video)}"></video>' if rel_video else ''}
<h2>Checks</h2><ul>{errs}{warns}</ul>
<h2>Review checklist</h2><ul>
<li>Story reads clearly with sound OFF (subtitles + acting)?</li><li>Every speaking puppet animates while its line plays?</li>
<li>Names / Sanskrit words spelled & highlighted correctly?</li><li>No puppet cut by frame edge or hidden behind subtitles?</li>
<li>Music ducks under narration; SFX land on the action?</li><li>Shot length & camera moves vary (no 3 static shots in a row)?</li>
<li>Thumbnail-worthy frame exists (pick from below)?</li></ul>
<h2>Shots</h2>{''.join(shot_html)}
<h2>Subtitles</h2><div class="wrap"><table><tr><th>shot</th><th>time</th><th>line</th><th>cps</th><th>flags</th></tr>{sub_rows}</table></div>
</body></html>"""
    path.write_text(page, encoding="utf-8")
