# Camera language & layered 2.5D motion (matched to the reference)

## What the reference does (measured from the source video)

- **Long continuous takes.** Only ~17 hard cuts in 13 minutes. Scenes flow by slow camera moves and soft
  dissolves; the camera is never fully still (slow drift/breathing).
- **Lateral trucking with deep parallax.** The camera slides sideways across a set; far mountains barely move,
  mid trees move more, and dark foreground posts / banana leaves sweep past fast and soft-focused.
- **Foreground wipes between sets.** A big dark foreground element (banana leaves, a pillar, a tree) crosses
  the lens and the next set is revealed behind it.
- **Crane-downs and push-ins.** Shots open on the sky (hanging sun/clouds) and descend to the puppets, or start
  wide on the set and push slowly toward the speaker.
- **Follow moves.** When a character walks, the camera travels with them; the set scrolls behind.
- **Lights-down silhouettes.** Mid-shot, the stage lights dim and the puppets turn into dark silhouettes
  against the glowing backdrop (story-within-story, dramatic beats).
- **Living backdrop.** Leaves/grass sway, swirl-clouds blow across, birds fly, animals pass in the distance.

## Camera moves (`camera.move`)

| move | what it does | use for |
|---|---|---|
| `drift` | slow, small push + slide (default) | narration over a set |
| `push_in` / `pull_out` | zoom in / out | emphasis / ending a beat |
| `pan_left` / `pan_right` | slide at constant zoom | revealing the set |
| `truck_left` / `truck_right` | **wide lateral move — strongest parallax** | travel, establishing, transitions |
| `crane_down` / `crane_up` | from sky (hanging sun/clouds) down to the stage / reverse | opening a scene / divine ending |
| `establish` | wide set → push onto `on:` character | first shot of a scene |
| `reveal` | tight on `on:` → pull back to the whole set | revelation, virat roop |
| `push_to` | slow push onto a character's face | emotional line, decision |
| `follow` | tracks `on:` character (with lag) | walking, flying, chasing |
| `float` | dreamy handheld drift | memory, divine, shadow screen |
| `tilt_up` / `tilt_down` | vertical | tall deities, mountains |
| `close_up` | fixed tight framing | quick reaction |
| `dolly_zoom` | push in on a character with rising frame | shock/realisation |
| `static` | no move (breathing still on) | rarely — titles |

Options: `on: <cast id>` (target), `frame: wide|full|medium|close|extreme` (zoom on the target),
`from`/`to` (zoom), `x`/`y` ([start, end] camera centre 0..1), `ease` (`inout`, `linear`, `out`, `back` …),
`shake` (constant), `breathe: false` (disable micro-drift).

```yaml
camera: {move: establish, on: arjuna, frame: medium}
camera: {move: follow, on: bhima, frame: full}
camera: {move: truck_right, from: 1.12, to: 1.18}
camera: {move: crane_down}
```

## Transitions (`transition:` on the incoming shot)

| transition | effect | default length |
|---|---|---|
| `crossfade` | soft dissolve (default) | 0.6 s |
| `wipe` | **foreground wipe**, element chosen from the env: banana leaves (forests, gardens, ashram, village), pillar (palace, temple, yagya, Lanka, Dwarka, Patala), cream cloud (Swarga, Kshirsagar, Kailash, cosmic), dark tree (everything else) | 1.3 s |
| `wipe_leaf` / `wipe_pillar` / `wipe_tree` / `wipe_cloud` | force the element | 1.3 s |
| `dip` | dip through black (time jump) | 0.6 s |
| `flash` | white flash (divine / battle impact) | 0.6 s |
| `cut` | hard cut | — |

`trans_dur:` overrides the length.

## Lighting events (`fx:`)

- `dim@t` (or `silhouettes@t`, `lights_down@t`): over 1.2 s the stage lights drop; puppets become silhouettes,
  the backdrop keeps glowing. `lights_up@t` brings them back.
- `flash@t`, `lightning@t`, `divine_burst@t`, `shake@t`, `fade_in@t`, `fade_out@t`.

## Layered 2.5D depth

Each environment = 6 parallax layers: sky (0.08) · far (0.28, blurred, hazy) · mid (0.55) · set (0.82) ·
ground (1.0, puppets live here) · front (1.3, dark, soft-focus). Cast members can sit at any depth
(`depth: 0.6` = further back, smaller, hazier, less parallax). Truck/pan moves make the layers slide at
different speeds — the core of the 2.5D look.

## Living background (automatic)

- **Wind**: trees, banana leaves, grass, reeds, wild flowers and foreground foliage sway with gusts that travel
  across the set (phase depends on x). Lotus pads bob, flags and banners flutter.
- **Ground flora**: grass tufts, reeds and flower clumps are scattered along the stage floor of natural sets,
  plus dark foreground clumps at the frame edges.
- **Sky**: puffy clouds drift slowly; a swirl wind-cloud blows across on windy day/dusk sets; birds fly.
- **Ambient creatures** (per locale & time): deer running/grazing, peacocks, butterflies, cows & calves, dogs,
  hens, swans gliding, fish leaping, cranes, parrots, eagles/vultures/kites circling, wolves & jackals at night,
  bats in caves, marching soldiers and galloping chariot horses at Kurukshetra, guards on Lanka's walls.
  Full table: `environments.md`.

Per shot:
```yaml
life: false                                     # quiet shot (no background creatures)
life:                                           # add your own
  - {who: elephant, mode: walk_across, depth: 0.55, speed: 0.04, period: 20}
  - {who: parrot, mode: fly_across, depth: 0.8, y: 0.3}
  - {who: deer, mode: graze, depth: 0.6, x: 0.85}
```
Modes: `run_across`, `walk_across`, `march` (n soldiers), `graze`, `peck`, `perch`, `glide` (on water),
`fly_across`, `circle` (soaring), `hover` (butterflies/bats), `leap` (fish). Options: `depth`, `x`, `y`,
`speed` (frame widths/s), `period` (s between passes), `n`, `scale`.

## Recipes in the reference style

```yaml
# Scene opening
- camera: {move: crane_down}
# A character walks to another
- camera: {move: follow, on: bhima, frame: full}
# Change of set
- transition: wipe
  camera: {move: truck_right}
# Revelation
- transition: flash
  camera: {move: reveal, on: hanuman, frame: medium}
  fx: ["divine_burst@0.6", rays, petals]
# Story-within-a-story
- env: shadow_screen_night
  transition: dip
  camera: {move: float}
  fx: ["dim@0.4"]
```
