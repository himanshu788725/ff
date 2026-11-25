# Art direction — the painted 2.5D puppet-theatre look

## The world is a stage

- **Puppets, not cartoons.** Flat, folk-painted (Kalamkari / Pattachitra / Cheriyal palette) cut-paper figures,
  dark-brown outlines, gouache texture, inner edge shading, gold rivets at shoulder/elbow/knee, thin cream
  strings rising to an unseen fly-bar. They sway like pendulums; walking is a gentle *hop*.
- **Heads in profile, bodies 3/4**: big almond eye with kohl flick, long nose line, curled moustache, kundal
  earrings, tilak. Crowns are tall stacked gold kirita mukut with a red/green plume at the back.
- **Scenery hangs from strings**: scalloped Kalamkari clouds with spiral curls, a rayed sun disc with concentric
  rings, crescent moon, stars. They drift ±2°.
- **Flats in layers**: sky → far mountains/city (hazy, blurred) → mid trees/buildings → set pieces → stage
  floor → dark blurred foreground leaves. The camera's parallax sells the 2.5D.
- **Light**: a warm spotlight from above-centre, heavy warm-brown vignette, darker fly-loft at the top, drifting
  smoky haze near the horizon, dust motes, god-rays, soft rim glow around puppets, drop shadows on the backdrop,
  flickering diyas and fire pools. Night = indigo with fireflies; fire = embers; divine = gold + petals.
- **Frame furniture**: red velvet curtain with scalloped valance, white pillars, diya footlights and audience
  head silhouettes for the opening/closing; shadow-screen with red border and pennant bunting for
  story-within-a-story.
- **Finish**: film grain, slight lamp flicker, gentle sharpening (done at master).

## Palette (named colours usable everywhere)

ochre `ochre` · mustard `mustard` · saffron `saffron` · vermilion `vermilion` · maroon `maroon` · indigo
`indigo` · peacock `peacock` · teal `teal` · mint `mint` · leaf `leaf` · olive `olive` · cream `cream` · gold
`gold` · ink `ink` · Rama blue `rama` · Krishna blue `krishna` · Shiva ash-blue `shiva` · monkey gold `monkey`.

## Iconography cheat-sheet

| figure | must-haves |
|---|---|
| Vishnu / Narayana | blue, 4 arms: chakra, shankh, gada, padma; halo; yellow dhoti |
| Rama | blue/teal, bow + arrow, kirita; vanvas: jata + valkal |
| Krishna | dark blue, peacock feather crown, bansuri (or sudarshan in war), yellow dhoti |
| Shiva | ash-blue, jata with crescent & Ganga, third eye, snake, rudraksha, tiger skin, trishul + damru |
| Brahma | golden, extra heads, beard, kamandalu, pothi, mala, lotus; hamsa |
| Ganesha | elephant head, one tusk, pot belly, modak, pasha/ankusha; mooshak |
| Kartikeya | six heads, vel (shakti), peacock |
| Hanuman | monkey face with cream muzzle, gold body, red dhoti, gada, tail, kirita |
| Durga | 8–10 arms of weapons, trishul, lion/tiger, red saree |
| Kali | dark skin, mundamala, khadga, tongue/fangs |
| Saraswati | white saree, veena, pothi, mala, hamsa |
| Lakshmi | red saree, lotus, gold coins (kalash), elephants, owl |
| Rishis | old build, white beard, jata, valkal, rudraksha, danda + kamandalu |
| Rakshasas | dark skins, round eyes, fangs, horns/spiky crown, big moustache, giant build |
| Ravana | ten heads (main + 9), 4+ arms, sword |

## Composition

- Stage x: 0.2–0.8 for main puppets; 0.1/0.9 for edge characters; off-stage entrances from -0.2 / 1.2.
- Ground line is at 84.5 % of the height (74 % for 9:16) — subtitles sit below it. Do not put faces lower than 70 %.
- Two-shot: 0.3 and 0.68 facing each other. Three-shot: 0.22, 0.5, 0.78 with the speaker in the middle.
- Depth: `depth: 0.7` for background crowds (smaller, hazier, less parallax); `depth: 1.2` for a looming foreground figure.
- Raised platforms (chariot, throne): `y: 0.74` and draw the platform with `layer: over`.
- Hanging sun/moon come with each env (top-right). Leave headroom: crowns are tall.

## Shot recipes

- **Opening**: curtain intro → establishing env with `pan_right`, birds, no dialogue.
- **Darshan**: `pull_out`, `grade: swarna`, `fx: ["divine_burst@0.5", rays, petals]`, deity `appear` + `bless`,
  devotee `namaste` → `bow`.
- **Battle**: `kurukshetra_dusk` (+ `music: {mood: epic_battle}`), chariot `layer: over`, horses `rear`, archers
  `shoot`, `fx: ["shake@x", dust]`, `sfx: conch, war_drums, arrows_volley`.
- **Night camp / storytelling**: `war_camp_night` or `shadow_screen_night`, listeners `pose: seated`, fire.
- **Sorrow**: `dusk`/`night`, `sad keep`, `music: {mood: sorrow}`, slow `drift`, longer `pad`.
- **Vertical Short**: `format: "9:16"`, characters `scale: 1.2–1.35`, `close_up` and `push_in` moves, `pop` subtitles.
