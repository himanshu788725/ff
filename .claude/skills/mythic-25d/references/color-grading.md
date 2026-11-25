# Colour grading & film finish

Grading happens **in-engine on every frame** (stills match the film) and the finish happens at master.

## Presets (`grade:` per film or per shot; `auto` picks by environment time)

| preset | look | auto for |
|---|---|---|
| `kathaa` | warm aged-paper puppet theatre: brown lifted shadows, creamy highlights, −14 % saturation | day, snow |
| `kathaa_night` | deep indigo shadows, warm lamp highlights | night |
| `agni` | hot oranges, crushed warm shadows | fire |
| `rakt` | battlefield dusk, blood-red sky, smoky browns | dusk |
| `neel` | moonlit blue | cosmic, storm |
| `swarna` | divine gold glow | divine |
| `smriti` | faded sepia flashback | — |
| `prabhat` | soft rose & gold dawn | dawn |
| `van` | forest green-gold | — |
| `natural` | minimal | — |

Each preset = S-curve contrast, per-channel gamma, lift (shadow colour), gain (highlight colour), saturation.
Edit or add presets in `engine/mythic25d/grade.py` (`GRADES`).

## Light rig (per shot `light:`)

`spot` (x, y of the warm stage light), `spot_color`, `vignette` (0.5 day … 0.8 night), `amb` (overall
exposure), `rays` (god-rays 0–1), `haze_k` (drifting haze strength). Example dramatic close-up:
`light: {vignette: 0.8, spot: [0.62, 0.38], rays: 0.6}`.

## Film finish (master)

`grade.ffmpeg_finish_filter(grain=6, sharpen=0.3, flicker=0.012)` adds lamp flicker (two slow sines on
brightness), unsharp 0.3, temporal luma/chroma grain; master caps bitrate at ~14 Mbps (1080p). Increase grain to 10 for a more 16 mm feel; set flicker 0
for a cleaner look.

## LUTs for other software

`mythic.py lut all --out luts/` writes `mythic_<preset>.cube` (33³) — use in DaVinci Resolve, Premiere,
Final Cut, OBS or ffmpeg (`-vf lut3d=mythic_kathaa.cube`) to match live-action or other footage to the films.
