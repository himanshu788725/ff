---
name: mythic-25d
description: Make painted 2.5D Indian-mythology puppet-theatre films (kathputli / paper-cut string puppets, hanging cloud & sun props, red-curtain stage, shadow-screen scenes) from a Hindi script — with 600+ ready characters (Tridev, Devis, Dashavatar, Devas, Ramayana, Mahabharata, rishis, rakshasas, nagas), 117 animals & birds, 110 environments, reference-style camera moves with layered parallax and a living animated background, Hindi Devanagari word-timed subtitles, Hindi neural voice, procedural raga music + SFX, first-pass mix, colour grading, review and troubleshooting. Use for any Hindi/Sanskrit mythological video, Ramayana/Mahabharata/Puranic story animation, YouTube long-form (16:9) or Shorts/Reels (9:16), shloka explainer, or when the user asks for this puppet/painted 2.5D style.
---

# Mythic 2.5D — painted puppet-theatre film skill

Everything runs from one CLI: `python <SKILL_DIR>/mythic.py <command>` (SKILL_DIR = the folder this file is in;
in this repo `.claude/skills/mythic-25d`). Projects live in `./mythic_projects/<name>/`.

The look (match it — see `references/art-direction.md`): bevelled, thick-outlined folk-painted cut-paper puppets
with segmented limbs and rivet joints that glow against a dimmer set (they pop out — 2.5D, not flat 2D), and
thin strings to the fly-bar, tall stacked gold mukut with a red plume, Kalamkari dotted trees/banana groves,
props hanging on strings (scalloped clouds, rayed sun, crescent moon), warm lamp-lit stage with heavy vignette,
drifting haze, dust motes, god-rays, film grain; red velvet curtain intro/outro with diya footlights and audience
silhouettes; shadow-screen (Tholu Bommalata) scenes; small subtitles at the bottom with the spoken word lit gold.
Camera language like the reference (see `references/camera-and-motion.md`): long continuous takes, slow
truck/crane/push moves with deep 6-layer parallax, foreground wipes (banana leaves / pillars) between sets,
follow moves on walking puppets, lights-down silhouettes — and a living backdrop (wind in trees/grass/flowers,
drifting clouds, deer/peacocks/swans/birds/soldiers moving in the distance), all automatic per environment.

## Workflow (do these in order)

1. **Check the machine once**: `mythic.py doctor` (ffmpeg with libass, fonts, edge-tts). Fix anything red using
   `references/troubleshooting.md`. Install deps: `pip install -r <SKILL_DIR>/requirements.txt`.
2. **Create the project**: `mythic.py new <name> [--format 9:16] --title "<हिंदी शीर्षक>"`.
   Save the user's Hindi script to `mythic_projects/<name>/script.txt`.
3. **Write `storyboard.yaml` from the script** — this is your main creative job. Follow
   `references/script-to-storyboard.md` (shot splitting, pacing, camera variety, acting) and the schema in
   `references/storyboard-schema.md`. Pick ids from `references/catalog-index.md` (characters/animals/birds) and
   `references/environments.md` (envs, props, actions, moods, SFX). Use `mythic.py search <hindi or english>` when unsure.
   Never invent ids — `validate` rejects unknown ones.
4. **Validate**: `mythic.py validate <proj>` → fix every ✘.
5. **Voice + word timings**: `mythic.py voice <proj>` (edge-tts Hindi neural voices, word boundaries → word-timed subs).
   Own recordings: set `audio:` per line and `voice.engine: files` (aligned automatically).
6. **Look-dev before the full render**: `mythic.py still <proj> --shot <id> --quality preview` for 2–3 key shots;
   open the JPGs and fix composition (overlaps, crops, puppets hidden by subtitles, wrong facing) in the storyboard.
7. **Preview film**: `mythic.py make <proj> --quality preview` (render → mix → master → review, ~1.5 min per minute
   of film on 4 cores). Read the printed review + `review/qa.json`, open `review/index.html`, fix, repeat.
8. **Final**: `mythic.py make <proj> --quality final` (1080p, or 1080×1920 for Shorts). Outputs in `out/`:
   `<name>_final.mp4` (burned Hindi subs), `<name>_clean.mp4` (no subs), `subs/subs.srt` (YouTube CC),
   `audio/stems/` (vo, music, sfx, ambience for re-mixing).

Single steps when iterating: `render`, `subs`, `mix`, `master`, `review`, `still`, `music` (see `mythic.py -h`).
Render only some shots: `mythic.py render <proj> --shots s3,s4`.

## Rules that keep quality high

- 4–9 s per shot for narration, 2–4 s for reaction/insert shots; a camera move on every shot. Think like the
  reference: open a scene with `crane_down` or `establish` (on the speaker), `follow` walking characters,
  `push_to` for emotional lines, `truck_left/right` for travel, `reveal` for divine moments; change sets with
  `transition: wipe` (foreground leaves/pillars) or a slow `crossfade`; `dip` for time jumps.
- Use `fx: ["dim@t"]` for story-within-story / dramatic beats (puppets become silhouettes against the lit backdrop).
- The background animates by itself (wind, clouds, animals). Add specific creatures with a shot `life:` list,
  or `life: false` for a quiet, focused shot.
- Every speaking character must be in that shot's `cast` with an `id` matching the line's `who` → it auto-talks.
- Give puppets real acting: `walk` in/out, `point`, `bless`, `namaste`, `strike`, `shoot`, `fly`, `appear`,
  `grow`, `fall`, `angry`, `sad`... Face characters toward each other (`face: left|right`).
- Keep important puppets between x 0.2–0.8 and above the subtitle band; seated puppets use `pose: seated` or `meditate`.
- Use the reference grammar: curtain intro on long-form, a shloka card (`shloka:`) when quoting scripture,
  shadow-screen env for flashbacks/legends-within-legends, hanging sun/moon/clouds come with each env.
- Hindi text: write natural Devanagari with proper punctuation (। , — ? !). Names in `highlight:`.
  Do not add letter-spacing to ASS styles — it breaks Devanagari shaping (matras become ◌).
- Shorts (9:16): 30–55 s, hook in the first 2 s, `subtitles.style: pop`, bigger puppets (`scale: 1.2`).
- Music/SFX/voice here are royalty-free generated assets. If the user supplies licensed music or real SFX:
  `music: {file: ...}`, drop SFX files into `<proj>/sfx/<name>.wav` — they override the synthetic ones.
- Respect the material: correct iconography (attributes, vahanas, colours) — see `references/art-direction.md`.

## Extending

- New character: add to the storyboard `characters:` section (`{base: <id>, ...overrides}` or a full spec) —
  fields in `references/storyboard-schema.md#characters`. Permanent additions: edit `engine/tools/gen_catalog.py`,
  run it, then `engine/tools/gen_docs.py`.
- New environment/prop/action/grade: see the matching module in `engine/mythic25d/` (`envs.py`, `props.py`,
  `actions.py`, `grade.py`); caches rebuild automatically when code changes.
- Pose sheet of any character: `mythic.py char hanuman`; gallery: `mythic.py gallery --cat devi`;
  environment preview: `mythic.py env kurukshetra_dusk`; LUTs for Resolve/Premiere: `mythic.py lut all`.

Human-readable bilingual manual: `docs/Mythic25D_Manual.pdf` (rebuild with `engine/tools/make_manual.py`).

## References (read when needed)

| file | when |
|---|---|
| `references/script-to-storyboard.md` | turning a Hindi script into shots (always, step 3) |
| `references/storyboard-schema.md` | every storyboard field |
| `references/catalog-index.md` | all 719 character/animal/bird ids by category |
| `references/environments.md` | 110 envs, props, actions, music moods, SFX, grades |
| `references/camera-and-motion.md` | reference camera moves, wipes, silhouettes, living background, `life:` |
| `references/art-direction.md` | the visual language, iconography, composition, shot recipes |
| `references/subtitles-voice.md` | Hindi word-timed subtitles, voices, own recordings, shloka cards |
| `references/audio-mixing.md` | music, SFX, ducking, loudness, stems |
| `references/color-grading.md` | grade presets, LUT export, film finish |
| `references/review-checklist.md` | what to check before delivering |
| `references/troubleshooting.md` | errors, slow renders, broken Hindi text, TTS failures |
