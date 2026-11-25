# Hindi voice + Devanagari word-timed subtitles

## Pipeline

```
storyboard (narration + lines) ──voice──► audio/vo/*.mp3 + audio/timing.json (every word: start/end)
                                           │
compile_plan ◄─────────────────────────────┘  (absolute times, auto talk animation, auto SFX)
   │
   ├─ subs/subs_<W>x<H>.ass  (karaoke / keyword / pop / line + shloka card + curtain titles)
   ├─ subs/subs.srt          (line-level, for YouTube CC / translation)
   └─ master: ffmpeg `ass` filter (libass + HarfBuzz) burns the subtitles with the bundled fonts
```

## Voice engines (`voice.engine`)

- **edge** (default): Microsoft Edge neural voices through `edge-tts` (free, needs internet). Hindi voices:
  `hi-IN-MadhurNeural` (male, warm narrator) and `hi-IN-SwaraNeural` (female). Word boundaries come from the
  TTS itself → subtitles are frame-accurate. Prosody per voice: `rate: "-6%"`, `pitch: "-2Hz"`.
  Casting defaults: female → Swara; child → Swara +18Hz; rakshasa/asura → Madhur −22Hz; elderly → Madhur −8Hz.
  Override per speaker in `voice.cast`.
- **files**: your own recording per line (`narration_audio:` / `lines[].audio:`). Words are aligned with
  faster-whisper when installed (`pip install faster-whisper`), otherwise with the built-in energy aligner
  (finds the speech span and distributes words by Devanagari syllable weight, snapping to pauses).
- **none**: no audio; timings are estimated (~6.6 aksharas/s) — fine for animatics and silent previews.

`voice` caches by text+voice — editing one line only re-synthesises that line. `voice --force` redoes all.
If edge-tts fails (offline/blocked), timings fall back to estimates and the review warns you.

Other TTS (ElevenLabs, Azure, Google, your studio VO): generate WAVs per line, put them in the project, use
`engine: files`.

## Subtitle styles

| style | look | best for |
|---|---|---|
| `karaoke` | full line; current word gold, spoken words cream, upcoming words dim; names mint | long-form narration (default 16:9) |
| `keyword` | the reference look: whole line fades in, names/keywords in mint | calm storytelling |
| `pop` | 1–2 big words at a time with a scale pop, centred low | Shorts/Reels (default 9:16) |
| `line` | plain line with fades | minimal |

Line breaking is balanced (no lonely last word), breaks prefer । , — ? !. Limits: `max_chars` (38 / 22 for
9:16), `max_words` (7 / 4). Narration colour vs dialogue colour differ slightly so viewers know who speaks.

## Fonts (bundled, SIL OFL)

Tiro Devanagari Hindi (default, elegant serif), Noto Serif Devanagari, Yatra One (bold display — pop style),
Rozha One (titles), Cinzel (Latin labels). They live in `engine/mythic25d/fonts/` and are passed to libass via
`fontsdir`, so they work without installing them system-wide.

**Never use letter spacing** (`\fsp`, style Spacing) with Devanagari: libass then shapes per glyph and the
matras/conjuncts break into dotted circles (◌). The generator keeps Spacing at 0.

## Shloka card

`shloka:` draws a dark top band with: source line, verse lines (large), small word glosses under chosen words
(positions measured with the real font), and the Hindi meaning. Keep 1–2 verse lines, 7–9 s on screen, and
have the narration paraphrase the meaning.

## Common fixes

- Words appear too early/late → check `audio/timing.json`; for own recordings install faster-whisper or trim
  leading silence; adjust `lead`.
- A line is too long/fast (review warns cps > 20) → shorten the sentence or split the shot.
- Speaker doesn't move → their cast `id` must equal the line `who`.
