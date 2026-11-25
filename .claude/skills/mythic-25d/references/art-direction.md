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

## Why the puppets pop (2.5D, not flat 2D) — built into every render

1. **Thick dark cut-paper outline** around every separate limb piece (`gfx.CHAR_STYLE`: ow 0.58 units), so
   overlapping segments read as layered paper.
2. **Volume shading** on each piece: edges darken (inner), lower-right edges shade (bevel), upper-left edges
   catch light (rim) — a bevelled, painted cut-out instead of flat fill.
3. **Segmented limbs with rivets**: upper arm / forearm / hand-prop, thigh (dhoti) / shin+foot for people,
   upper leg / lower leg+hoof for animals, each pinned at a rivet; knees bend when walking.
4. **Lit puppet against a dim set** (`render.pop_light`): wide warm aura + bright tight rim glow around the
   silhouette, light wrap on the edges, +14 % saturation; the set behind is dimmed (≈0.8) and desaturated (0.8).
5. **Warm darkness**: nights are dark warm browns (not blue), with lamp-lit puppets.

Tune per shot: `light: {bg_dim: 0.75, bg_desat: 0.7}` for more pop, `bg_dim: 0.95` for a brighter set.
Edit `CHAR_STYLE` in `engine/mythic25d/gfx.py` to change outline thickness / bevel globally.

## Puppet anatomy (every humanoid is built from these pieces)

| piece | detail |
|---|---|
| crown (`heads._kirita`) | stacked rounded gold rings narrowing upward, gems on every tier, lotus-bud finial, jewelled base band, red flame plume behind |
| face | profile, big almond eye with kohl flick, long nose line, curled moustache (men), tilak; women add a large nath ring and jhumka |
| ear | round gold **kundal disc** with a vermilion gem on the cheek (the reference's most recognisable jewel) |
| hair | men: long locks with highlight strands down the back; women: long braid with gajra flowers and a red tassel; rishis: tall jata dome |
| torso | collarbones, multi-strand necklaces with drops/pearls, sacred thread or crossed straps (`straps: true`), beaded belt with tassels |
| body lines | dark skin (Bhima, Kali, rakshasas) gets light gold body lines; light skin gets darker lines |
| arms | capsule upper arm with shoulder cap and double bajuband → forearm with bangles → separate hand, rivets at shoulder/elbow/wrist; weapons sit in the hand |
| waist | dhoti/lehenga with pattern, striped front flap with a tassel |
| legs | thigh (dhoti) → shin + foot with anklets, rivet at the knee |
| seat | `pose: seated` sits on a red cushion with gold stripe on a dark stone block; women sit side-saddle |
| extras | extra arms fan behind with their own hands and weapons; Ravana-style extra heads fan in an arc around the crown; quiver appears automatically with a bow; tails are segmented with rivets |

Fields that change this look per character: `skin`, `crown`, `crown_color`, `plume`, `tiers`, `hair`, `beard`,
`dhoti`, `saree`, `straps`, `strap_color`, `necklace`, `pearls`, `arms`, `heads`, `items`, `seat`
(see `storyboard-schema.md#characters`).

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
| Ravana | ten heads (main + 9), burnt-orange skin, green dotted dhoti, ten arms of weapons |

## Composition

- Stage x: 0.2–0.8 for main puppets; 0.1/0.9 for edge characters; off-stage entrances from -0.2 / 1.2.
- Ground line is at 84.5 % of the height (74 % for 9:16) — subtitles sit below it. Do not put faces lower than 70 %.
- Two-shot: 0.3 and 0.68 facing each other. Three-shot: 0.22, 0.5, 0.78 with the speaker in the middle.
- Depth: `depth: 0.7` for background crowds (smaller, hazier, less parallax); `depth: 1.2` for a looming foreground figure.
- Raised platforms (chariot, throne): `y: 0.74` and draw the platform with `layer: over`.
- Hanging sun/moon come with each env (top-right). Leave headroom: crowns are tall.

## Shot recipes (camera grammar: see camera-and-motion.md)

- **Opening**: curtain intro → `crane_down` from the hanging sun/clouds onto the set, no dialogue; next shot
  `establish` on the first speaker.
- **Travel**: `transition: wipe` + `truck_right`, or `follow` the walker; background deer/birds keep moving.
- **Darshan**: `pull_out`, `grade: swarna`, `fx: ["divine_burst@0.5", rays, petals]`, deity `appear` + `bless`,
  devotee `namaste` → `bow`.
- **Battle**: `kurukshetra_dusk` (+ `music: {mood: epic_battle}`), chariot `layer: over`, horses `rear`, archers
  `shoot`, `fx: ["shake@x", dust]`, `sfx: conch, war_drums, arrows_volley`.
- **Night camp / storytelling**: `war_camp_night` or `shadow_screen_night`, listeners `pose: seated`, fire.
- **Sorrow**: `dusk`/`night`, `sad keep`, `music: {mood: sorrow}`, slow `drift`, longer `pad`.
- **Vertical Short**: `format: "9:16"`, characters `scale: 1.2–1.35`, `close_up` and `push_in` moves, `pop` subtitles.
