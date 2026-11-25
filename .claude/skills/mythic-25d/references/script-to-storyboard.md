# Script → storyboard (Claude's creative pass)

Goal: a film that reads like a lamp-lit puppet performance — every sentence has a picture, every speaker
moves, the camera breathes, and the scenery changes with the story's place and time of day.

## 1. Read and beat the script

1. Split the Hindi script into **beats**: one beat = one idea/visual (usually one sentence or two short ones).
2. Mark: places (→ env), time of day (→ env time), characters on stage (→ cast), who speaks (→ `lines`),
   verses quoted (→ `shloka`), big moments (→ fx: flash, divine_burst, shake, lightning).
3. Target **8–12 shots per minute** for long-form, **6–8 per 45 s** for Shorts.

## 2. Each beat → one shot

| beat type | env & camera | cast & acting |
|---|---|---|
| establishing a place | wide env, `drift` or `pan_*`, 4–6 s, maybe no cast | birds/animals, a hanging sun/moon |
| narration about a character | `push_in` toward them | idle + one gesture (`bless`, `point`, `raise`) |
| dialogue | two characters facing each other, x≈0.3 & 0.68; `drift`/`close_up` | speaker auto-talks; listener reacts (`namaste`, `angry`, `laugh`) |
| travel / arrival | `pan_right` with the walk direction | `walk` from off-stage (x -0.2 → 0.3) |
| battle beat | kurukshetra / war_camp / lanka_fire, `push_in` + `shake@` | `strike`, `shoot`, `fight`, `fall`; horses `rear` |
| divine revelation | `pull_out`, grade `swarna`, fx `divine_burst@`, `rays`, `petals` | `appear`, `grow`, `raise_both`; devotees `namaste`/`bow` |
| memory / story-within-story | `shadow_screen_night`, `drift` | `shadow_puppet: true` silhouettes; listeners seated around fire |
| scripture quote | calm env, `static`/`drift`, 7–9 s | `shloka:` card; speaker `bless` |
| ending | curtain outro + chant text | `namaste`, `bless` |

Rules:
- Shot length follows the voice automatically (`duration: auto`). Split narration over ~22 words into 2 shots.
- Alternate camera moves; avoid two identical moves back to back; use `close_up` for emotional lines.
- Change the environment's time with the story (dawn → day → dusk → night) — it changes palette, light,
  hanging props and grade automatically.
- Put the camera's interest where the action is: `camera.x: [0.6, 0.58]` for a close-up on a character at 0.64.
- Keep cast ≤ 4 per shot (6 for crowds with `depth: 0.7` for back rows).
- Use catalog ids only; for an unlisted being pick the nearest and override (`{base: rakshasa_soldier, skin: "#2a4a4a"}`).
- Iconography matters: Rama/Krishna blue, Shiva ash-blue with jata, moon, snake, trishul; Hanuman with gada &
  kirita; Ganesha with modak; Durga 8-armed on a lion; Saraswati with veena on a hamsa; Lakshmi with lotus.

## 3. Writing the Hindi text

- Narration in simple, rhythmic Hindi (storyteller voice — "बहुत समय पहले…", "तभी…", "और फिर…").
- 12–22 words per narration, 4–14 words per dialogue line. Use । , — ! ? for natural pauses (TTS honours them).
- Sanskrit words in correct Devanagari; put names in `highlight` for coloured subtitles.
- Dialogue `who` must be a cast `id` in the same shot.

## 4. Sound design intentions

- Set the global `music.mood`; switch per shot with `music: {mood: epic_battle}` at the battle, `sorrow` for loss,
  `divine` for darshan. Two–four music sections per film is plenty.
- Actions/fx/envs add SFX automatically; add signature cues yourself: `conch` at war start, `ghanta` at temple,
  `damru` for Shiva, `horse_gallop` / `chariot_rumble` for chariots, `thunder` with `lightning@`.

## 5. Example (one beat → one shot)

Script: “भीम ने पूरी शक्ति लगा दी, पर वह पूँछ तिल भर भी नहीं हिली!”

```yaml
- id: s4_shakti
  env: forest_banana_day
  camera: {move: push_in, from: 1.05, to: 1.18, x: [0.45, 0.48]}
  narration: "भीम ने पूरी शक्ति लगा दी — पर वह पूँछ तिल भर भी नहीं हिली!"
  cast:
    - {who: hanuman, x: 0.64, pose: seated, face: left}
    - {who: bhima, x: 0.36, face: right, actions: [{do: angry, at: 0.3, dur: 1.4}, {do: strike, at: 1.8, dur: 1.0},
                                                  {do: shake, at: 3.0, dur: 2.5, amount: 1.4}, {do: sad, at: 5.6, dur: 3, keep: true}]}
  fx: ["shake@2.4", dust]
```

## 6. After writing

`validate` → `voice` → `still --shot` on 2–3 key shots (look at them!) → `make --quality preview` → read the review →
adjust x positions, facing, timing (`at`) and camera → final.
