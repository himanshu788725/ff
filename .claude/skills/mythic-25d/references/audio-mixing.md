# Music, SFX and the first-pass mix

## Music (procedural raga score)

`render_music` builds a royalty-free bed: tanpura drone (Sa–Pa–Sa'–Sa, jawari bloom), a raga melody
(phrase-based improvisation around vadi/samvadi with meend glides) on bansuri / shehnai / santoor / sitar /
sarangi, tala on tabla (teental, keherwa, dadra) or dhol/nagara (battle), bells for sacred moods, a soft
choir/strings pad, convolution reverb. Sections: the global `music.mood` plus any shot with `music:` starts a
new section (2 s crossfade). Intro alaap (no percussion) for the first ~20 % of each section.

Moods → raga/tempo: devotional (yaman 72), divine (bhairav 60), epic_battle (kirwani 118), mystery
(malkauns 54), sorrow (bhairavi 56), sad (shivaranjani), forest (desh 80), royal (durga 92), tension (marwa 100),
triumph (durga 112), night (bageshree 62), auspicious (hamsadhwani 86), dance (desh 124), meditative,
romance (kafi), dawn (bhairav). `raga:` overrides; `key:` sets Sa (default C#).

It is a good temp/bed score. For a flagship video use a licensed track: `music: {file: music/track.mp3}`
(looped/trimmed, faded, ducked automatically).

## SFX

54 generated SFX (`mythic.py list sfx`): whoosh, arrow_whoosh, arrows_volley, mace_hit, sword_clash,
impact_boom, thunder, earthquake, conch, ghanta, temple_bells, bell_soft, divine_shimmer, magic_swell,
chakra_spin, damru, war_drums, nagara, horse_gallop, chariot_rumble, footsteps, body_fall, roar,
elephant_trumpet, horse_neigh, crow_caw, peacock_call, demon_laugh, curtain_swish, string_creak, splash,
heartbeat, crowd_cheer, gong + ambience beds: forest_birds, crickets, wind, river, ocean_waves, rain_storm,
fire_crackle, fire_big, campfire, cave_drips, palace_hum, village, battle_ambience, audience_murmur,
cosmic_drone, divine_pad.

**Automatic cues** (`auto_sfx: true`): actions (strike → mace_hit, shoot → arrow_whoosh, appear →
divine_shimmer, fly → whoosh_long, fall → body_fall, walk → footsteps, rear → horse_neigh, laugh →
demon_laugh ...), fx (`lightning@` → thunder, `flash@` → impact_boom, `shake@` → earthquake), an ambience bed
per environment (forest → birds, night → crickets, kurukshetra → battle ambience, ocean → waves ...), curtain
swish + conch + audience murmur for the theatre intro/outro.

**Real recordings beat synthesis** for animal calls and voices: put `horse_neigh.wav`, `elephant_trumpet.wav`,
`conch.mp3` ... into `<project>/sfx/` (or `~/.cache/mythic25d/sfx_user/`) — same name = automatic override.

## Mix (`mythic.py mix <proj>`)

1. VO chain (ffmpeg): high-pass 75 Hz, low-pass 14 kHz, +1.5 dB @220 Hz warmth, +2 dB @3.2 kHz presence,
   3:1 compression, a short "storyteller room" echo.
2. Music at `volume_db` (default −17 dB) with sidechain ducking under the voice (−10 dB, 80 ms attack,
   450 ms release); ambience beds duck −6 dB.
3. SFX at cue volume (default −10 dB; beds −22 dB with 1.2 s fades).
4. Soft limiter → two-pass EBU R128 loudnorm: **−14 LUFS, −1.5 dBTP** (YouTube). `--lufs -16` for podcasts/
   Spotify-style, `-23` for broadcast.
5. Writes `audio/mix.wav` and stems `audio/stems/{vo,music,sfx,ambience}.wav` for a DAW pass.

Fixes: music too loud → `music.volume_db: -20`; ducking too strong → edit `duck_db` in `mix.py`; an SFX too loud →
`vol` on the cue; disable an ambience → `ambience: false` on the shot.
