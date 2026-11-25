# Storyboard schema (`storyboard.yaml`)

```yaml
title: "हनुमान और भीम"          # used for intro title + file names
format: "16:9"                  # 16:9 | 9:16 | 1:1 | 4:5 | 4k
fps: 30                         # 24/25/30
grade: auto                     # auto = per env time-of-day; or a preset for every shot (see color-grading.md)
highlight: [हनुमान, भीम]        # global keywords for subtitles (names, places)
auto_sfx: true                  # SFX from actions/fx + ambience beds per environment
voice:
  engine: edge                  # edge | files | none
  narrator: hi-IN-MadhurNeural  # see `mythic.py list voices`
  rate: "-6%"                   # edge-tts prosody
  pitch: "-2Hz"
  cast:                         # per-speaker voice (else picked from character type)
    bhima: {voice: hi-IN-MadhurNeural, rate: "-2%", pitch: "-12Hz"}
    sita: hi-IN-SwaraNeural
music:                          # one bed; shots can switch mood (see shot.music)
  mood: devotional              # devotional divine epic_battle mystery sorrow forest royal tension triumph night auspicious dance meditative romance dawn
  raga: null                    # override raga (yaman, bhairav, malkauns, darbari ...)
  key: "C#"                     # tonic (Sa) of drone
  volume_db: -17
  file: null                    # path to your own track (looped/trimmed, faded, ducked)
subtitles:
  style: karaoke                # karaoke | keyword | pop | line
  enabled: true
  font: "Tiro Devanagari Hindi" # or "Noto Serif Devanagari", "Yatra One", "Rozha One"
  size: 56                      # px at output resolution (default 5.2% of height)
  margin_v: 60
  color: "#f4e9cf"              # narration
  dialog_color: "#f8d9a8"       # character lines
  highlight: "#f2c94a"          # active word
  keyword: "#9fe0c8"            # names / highlight words
  max_chars: 38                 # per line (22 for 9:16)
  max_words: 7                  # per line (4 for 9:16)
  pop_words: 2                  # pop style: words per flash
intro:                          # theatre curtain opening (long-form)
  curtain: true
  title: "हनुमान और भीम"
  subtitle: "महाभारत की एक कथा"
  label: "महाभारत ↗ वन पर्व"     # small top-right series label
  pre: 3.5                      # seconds of closed curtain with title
  open: 2.4                     # curtain opening duration
outro: {curtain: true, text: "॥ जय बजरंगबली ॥", subtitle: "...", post: 4.0, close: 2.0}
characters:                     # project-specific characters (optional)
  bhima_wounded: {base: bhima, dhoti: [maroon, dots, gold], angry: true}
  my_rishi: {kind: humanoid, build: old, crown: jata, beard: long, lower: valkal, skin: skin_light, items: {f: danda}}
shots: [...]
```

## Shot

```yaml
- id: s3                        # unique; used for file names & `--shots`
  env: forest_banana_dusk       # <locale>_<time>, see environments.md
  duration: auto                # auto = voice length + lead + pad; or seconds (minimum)
  lead: 0.35                    # silence before first line (0.6 on shot 1)
  pad: 0.7                      # breathing room after the last line
  transition: crossfade         # crossfade | dip | flash | cut   (into this shot)
  trans_dur: 0.6
  grade: swarna                 # override grade for this shot
  camera:
    move: push_in               # static push_in pull_out pan_left pan_right tilt_up tilt_down drift close_up
    from: 1.0                   # zoom at start (>=1)
    to: 1.12                    # zoom at end
    x: [0.5, 0.55]              # camera centre x (start, end) 0..1
    y: [0.5, 0.48]
    ease: inout                 # linear smooth inout out in back
    shake: 0.0                  # constant handheld shake
  narration: "हिंदी कथन ..."     # narrator text (spoken first)
  narration_audio: vo/s3.wav    # (voice.engine: files) your recording
  lines:                        # dialogue after narration, in order
    - {who: bhima, text: "हे वानर!", gap: 0.4, audio: vo/bhima_1.wav}
  highlight: [भीम]
  music: {mood: epic_battle}    # start a new music section at this shot
  ambience: wind                # override auto ambience bed (or false)
  cast: [...]
  props: [...]
  fx: [dust, rays, "flash@2.4", "lightning@1.0", "shake@3.0", "divine_burst@0.5", "fade_out@6"]
  sfx: [{name: conch, at: 0.3, vol: -6}, {name: war_drums, at: 1, vol: -14, dur: 5}]
  shloka: {...}                 # verse card, see below
  light: {spot: [0.5, 0.42], spot_color: "#ffcf8a", vignette: 0.7, rays: 0.5, haze_k: 0.2, amb: 0.9}
```

### cast member

```yaml
- who: hanuman                  # catalog id, or {base: id, ...overrides}, or full custom spec
  id: hanuman                   # defaults to who; must match `lines[].who` for auto-talk
  x: 0.4                        # stage x 0..1 (can start off-stage: -0.2 / 1.2)
  y: ground                     # 'ground' or a frame fraction for the feet (e.g. 0.74 = standing on a chariot)
  face: right                   # right | left
  pose: stand                   # stand | seated | meditate
  depth: 1.0                    # <1 further back (smaller, hazier, parallax), >1 nearer
  scale: 1.0
  strings: true                 # puppet strings to the fly bar
  shadow_puppet: false          # black silhouette (use on shadow_screen envs)
  z: 1.0                        # draw order override
  actions:                      # see environments.md → Actions
    - {do: walk, to: 0.7, at: 0.2, dur: 2.5}
    - {do: point, at: 3.0, dur: 2}
    - {do: talk, at: 4, dur: 3}           # usually automatic from lines
    - {do: bless, at: 7, dur: 2, keep: true}
```

Action timing `at` is seconds from the shot start. `keep: true` holds the pose until the shot ends.
Persistent effects carry forward inside the shot (walk moves x, sit/stand, fall leaves the body lying,
vanish leaves it invisible, turn changes facing). Every shot starts fresh from its own cast settings.

### props

```yaml
- {name: chariot, x: 0.45, layer: over, s: 2.0, emblem: hanuman, flag: mustard}  # over = drawn in front of puppets
- {name: cloud, hang: true, x: 0.2, y: 0.12, s: 1.2, kind: curl}                   # hangs on a string, sways
- {name: tree, x: 0.9, layer: ground, s: 1.2, kind: kadamba}
- {name: cushion, x: 0.5, layer: ground, s: 1.4}
```
Layers: `ground` (behind puppets, at the stage floor), `over` (in front of puppets, same depth — chariots,
throne fronts, altars), `front` (foreground, extra parallax). Prop params are the builder arguments in
`engine/mythic25d/props.py` (e.g. `tree(kind=banana|palm|pine|bamboo|kalamkari|mango|peepal|ashoka|kadamba|flowering|banyan|night)`,
`palace(wall, window, bays, interior)`, `flagpole(color, kind=banner, emblem)`, `tent(c1, c2)`, `boat(sail)`).

### shloka card

```yaml
shloka:
  source: "श्रीमद्भगवद्गीता · ४.७"
  lines: ["यदा यदा हि धर्मस्य ग्लानिर्भवति भारत ।", "अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम् ॥"]
  gloss: [[धर्मस्य, "धर्म की"], [ग्लानिर्भवति, "हानि होती है"]]   # small notes under words
  meaning: "जब-जब धर्म की हानि होती है, तब-तब मैं अवतार लेता हूँ।"
  at: 0.5
  dur: 7
```

## Characters (custom spec fields)

`kind` humanoid · `head` human|monkey|bear|elephant|lion|eagle|boar|horse|buffalo · `female` · `build`
hero|slim|heavy|female|old|child|giant · `skin` (named colour or #hex: rama, krishna, shiva, monkey, skin_tan,
skin_light, skin_brown, skin_dark ...) · `crown` kirita|kirita_low|peacock|jata|jata_shiva|tiara|bun|veil|turban|
horns|spiky|helmet|shikha|flames|sun|hoods|none · `hair` long|short|bald · `hair_color` · `beard` long|short ·
`beard_color` · `mustache` curl|big|plain|null · `tilak` vaishnav|shaiva|bindi|dot · `third_eye` · `eye`
almond|round · `fangs` · `angry` · `lower` dhoti|saree|tiger|valkal|armor|loin|serpent|fish · `dhoti`
[colour, pattern, pattern_colour] (patterns: dots stripes vstripes checks zigzag chevron scales floral tiger
leopard waves speckle) · `saree` [colour, pattern, border] · `choli` · `sash` · `armor` (colour) · `janeu` ·
`necklace` · `pearls` · `rudraksha` · `snake` · `mundamala` · `metal` · `items` {f: front-hand item, b: back-hand
item} · `arms` 2|4|6|8|10 · `extra_items` [...] · `heads` [extra head types] · `tail` · `wings` (+wing_color) ·
`halo` (+halo_color) · `hoods` · `tail_color` · `scale`.

Items: gada bow arrow trishul chakra sudarshan shankh padma damru khadga/sword dhal/shield vajra kamandalu mala
pothi bansuri veena pasha ankusha parashu hala danda shakti/spear dhwaja/flag chhatra diya kalash modak flower
chamara bag mirror, plus `abhaya`/`varada` (open blessing hand).

Animals: `{kind: quadruped, base: horse|cow|bull|buffalo|elephant|lion|tiger|leopard|deer|dog|wolf|boar|bear|goat|
ram|camel|donkey|rabbit|rat|cat|monkey|rhino|jackal, color, cloth, bells, pattern, scale}`;
birds: `{kind: bird, base: peacock|hamsa|eagle|vulture|owl|crow|parrot|crane|... , size, body, wing, head}`;
serpents: `{kind: serpent, hoods, color, length}`; fish: `{kind: fish, color, size}`.
