# Review checklist

`mythic.py review <proj> [--quality preview|final]` writes `review/index.html` (video player, per-shot
start/mid/end thumbnails, subtitle table with chars-per-second, checks) + `review/qa.json` +
`review/contact_sheet.jpg`, and prints errors/warnings. Read the printout, then look at the contact sheet.

## Automatic checks

- Devanagari font present; ffmpeg has libass (subtitle burn-in).
- Voice: real TTS/recording vs estimated timing.
- Shots: < 1.5 s (too short), > 25 s (split it), no cast (fine for establishing shots).
- Subtitles: > 20 chars/s (too fast), < 0.8 s on screen, over-long lines.
- Video: duration vs plan, black frames, near-static picture for > 3 s (add an action or camera move).
- Audio: integrated loudness within ±1.5 LU of −14 LUFS, true peak ≤ −0.5 dBFS, audio stream present.

## Human checks (look at the thumbnails / play the film)

1. Story reads with sound OFF (subtitles + acting + scenery).
2. Each speaker moves while talking; listeners react.
3. Faces/crowns not cut by the frame top; nobody hidden by subtitles or the shloka band.
4. Facing directions make sense (characters look at whom they address; entrances move toward the centre).
5. Iconography correct (attributes, colours, vahanas) and Hindi/Sanskrit spelling correct.
6. Camera variety — no three static shots in a row; transitions feel motivated (dip for time jumps, flash for
   divine/battle beats).
7. Music ducks under narration; SFX land on hits; ambience fits the place; no clipping.
8. Opening 3 seconds hook the viewer (Shorts: even the first second).
9. Pick a thumbnail frame (bright, a face + a prop, uncluttered) — `mythic.py still <proj> --t <sec> --quality final`.

## Fix loop

Edit storyboard → `mythic.py render <proj> --shots s4,s5` to iterate on a few shots → when happy run `make`.
