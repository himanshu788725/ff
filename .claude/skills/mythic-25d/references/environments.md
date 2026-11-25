# Environments, props, actions, moods (auto-generated)

## 110 environments  (`env: <locale>_<time>`)

Times: dawn · day · dusk · night · fire · divine · storm · cosmic · snow (each locale lists the ones it supports).

| locale | times | what it is |
|---|---|---|
| `palace_court` | day, night, dusk, divine | राजदरबार (Ayodhya/Hastinapur darbar) |
| `palace_garden` | day, dawn, dusk, night | राजउद्यान / अशोक वाटिका |
| `forest_banana` | day, dawn, dusk, night | कदली वन (banana forest) |
| `forest_deep` | day, dusk, night, storm | घना वन / दण्डकारण्य |
| `ashram` | dawn, day, dusk, night | ऋषि आश्रम (hut, yagya) |
| `yagya_shala` | day, night, dawn, divine | यज्ञशाला (agni yagya hall) |
| `kailash` | snow, dawn, night, divine | कैलाश पर्वत |
| `kshirsagar` | divine, day, night, cosmic | क्षीरसागर / वैकुण्ठ |
| `swarga` | divine, day, dusk, night | स्वर्ग / इन्द्रलोक |
| `patala` | night, fire, cosmic, dusk | पाताल लोक |
| `lanka` | day, dusk, night, fire | सोने की लंका |
| `ocean_shore` | day, dawn, dusk, night | समुद्र तट / राम सेतु |
| `kurukshetra` | dawn, day, dusk, night, fire, storm | कुरुक्षेत्र युद्धभूमि |
| `war_camp` | night, dusk, dawn, fire | युद्ध शिविर |
| `ghats` | dawn, day, dusk, night | गंगा घाट |
| `village` | day, dawn, dusk, night | गाँव / गोकुल |
| `mountain_pass` | day, dusk, night, snow | गंधमादन / हिमालय (sanjeevani) |
| `cave` | night, fire, day, cosmic | गुफा |
| `dwarka` | day, dusk, night, divine | द्वारका |
| `vrindavan` | day, dawn, dusk, night | वृन्दावन / यमुना तट |
| `temple` | night, day, dusk, divine | मंदिर गर्भगृह |
| `shmashan` | night, fire, storm, dusk | श्मशान |
| `cosmic` | cosmic, divine, night, fire | ब्रह्माण्ड / विराट रूप |
| `plain` | day, dusk, dawn, storm | खुला मैदान / मार्ग |
| `lotus_lake` | day, dawn, divine, night | कमल सरोवर |
| `stage` | night, day, fire, divine | कठपुतली मंच (theatre stage) |
| `shadow_screen` | night, fire, dusk, cosmic | छाया-नाट्य परदा (shadow theatre) |

## Props (`props:` in a shot)

`cloud` (hangs), `sun` (hangs), `moon` (hangs), `star` (hangs), `tree`, `bush`, `lotus`, `grass`, `rock`, `mountains`, `palace`, `pillar`, `temple`, `fort`, `city`, `hut`, `tent`, `flagpole`, `deepstambh`, `diya`, `yagya_kund`, `throne`, `chhatra` (hangs), `chariot`, `boat`, `pots`, `cushion`, `toran`, `bunting`, `waterfall`, `screen`, `cave`, `steps`, `setu`, `sanjeevani_mountain`

## Actions (`actions:` on a cast member)

| action | params |
|---|---|
| `walk` | to (x 0..1), dur, steps, face(auto|keep) |
| `run` | to, dur |
| `talk` | dur, gesture(bool) |
| `point` | dur, keep |
| `bless` | abhaya mudra; dur, keep |
| `namaste` | dur, keep |
| `bow` | deep pranam |
| `raise` | raise weapon arm |
| `raise_both` | both arms up (victory/prayer) |
| `strike` | mace/sword blow; dur |
| `shoot` | draw bow & release; dur |
| `throw` | throw spear/chakra |
| `fight` | repeated strikes; dur, period |
| `sit` | switch to seated (padmasana) |
| `stand` | back to standing |
| `meditate` | seated dhyana + aura |
| `fly` | to, dur, height, arc |
| `hover` | float in place; height |
| `jump` | height, dur, to |
| `fall` | collapse & lie (die/faint); back(bool) |
| `shake` | tremble; amount |
| `angry` | furious gesture |
| `dance` | bpm, dur |
| `laugh` | dur |
| `sad` | head down; keep |
| `appear` | divine entrance (fade+glow) |
| `vanish` | fade out upward |
| `hidden` | invisible until dur |
| `turn` | flip facing; face_to(1|-1) |
| `grow` | virat roop; to(scale), dur |
| `shrink` | to, dur |
| `move` | glide to x; dy |
| `glow` | aura; amount |
| `spin` | spin held chakra; part, speed |
| `pose` | raw angles dict |
| `silhouette` | on/off shadow-puppet look |
| `graze` | animal head down |
| `rear` | horse rears up |
| `roar` | lion/tiger roar |
| `peck` | bird pecks |

## Music moods

| mood | raga | bpm | lead | percussion |
|---|---|---|---|---|
| `devotional` | yaman | 72 | bansuri | tabla |
| `divine` | bhairav | 60 | bansuri | none |
| `epic_battle` | kirwani | 118 | shehnai | dhol |
| `battle` | kirwani | 118 | shehnai | dhol |
| `mystery` | malkauns | 54 | santoor | none |
| `sorrow` | bhairavi | 56 | sarangi | tabla_soft |
| `sad` | shivaranjani | 56 | sarangi | tabla_soft |
| `forest` | desh | 80 | bansuri | tabla_soft |
| `royal` | durga | 92 | shehnai | tabla |
| `tension` | marwa | 100 | santoor | pulse |
| `triumph` | durga | 112 | shehnai | dhol |
| `night` | bageshree | 62 | sitar | tabla_soft |
| `auspicious` | hamsadhwani | 86 | shehnai | tabla |
| `dance` | desh | 124 | santoor | dhol |
| `meditative` | yaman | 50 | sitar | none |
| `romance` | kafi | 76 | bansuri | tabla_soft |
| `dawn` | bhairav | 66 | bansuri | tabla_soft |

Ragas: `yaman`, `bhupali`, `bhairav`, `bhairavi`, `darbari`, `malkauns`, `marwa`, `desh`, `durga`, `bageshree`, `kirwani`, `shivaranjani`, `todi`, `hamsadhwani`, `kafi`, `puriya_dhanashri`

## SFX names

`arrow_whoosh`, `arrows_volley`, `audience_murmur`, `battle_ambience`, `bell_soft`, `body_fall`, `campfire`, `cave_drips`, `chakra_spin`, `chariot_rumble`, `conch`, `cosmic_drone`, `crickets`, `crow_caw`, `crowd_cheer`, `curtain_swish`, `damru`, `demon_laugh`, `divine_pad`, `divine_shimmer`, `earthquake`, `elephant_trumpet`, `fire_big`, `fire_crackle`, `footsteps`, `footsteps_fast`, `forest_birds`, `ghanta`, `gong`, `heartbeat`, `horse_gallop`, `horse_neigh`, `impact_boom`, `mace_hit`, `magic_swell`, `nagara`, `ocean_waves`, `palace_hum`, `peacock_call`, `rain_storm`, `river`, `roar`, `shankh`, `splash`, `string_creak`, `sword_clash`, `temple_bells`, `thunder`, `thunder_soft`, `village`, `war_drums`, `whoosh`, `whoosh_long`, `wind`

## Grades

- `kathaa` — Reference look: warm aged-paper puppet theatre, brown shadows, creamy highlights
- `kathaa_night` — Night puppet stage: deep indigo shadows, warm lamp highlights
- `agni` — Fire / yagya / burning Lanka: hot oranges, crushed warm shadows
- `rakt` — Battlefield dusk: blood-red sky, smoky browns
- `neel` — Moonlit blue night
- `swarna` — Divine golden glow (darshan, avatars)
- `smriti` — Flashback / memory: faded sepia
- `prabhat` — Dawn: soft rose & gold
- `van` — Forest: green-gold, earthy
- `natural` — Minimal grade
