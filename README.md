# Mythic 2.5D — painted Indian-mythology puppet-theatre films (Claude Code skill)

`.claude/skills/mythic-25d/` is a ready-to-use **Claude Code skill + render engine** that turns a Hindi script into a
painted 2.5D kathputli/paper-puppet film: jointed puppets on strings, hanging cloud/sun props, Kalamkari scenery,
red-curtain theatre intro, shadow-screen scenes, warm lamp-lit grade — with Hindi voice, Devanagari word-timed
subtitles, raga music, SFX, mix, colour grading and an automatic review page.

| | |
|---|---|
| characters | **602** humanoid (Tridev, Tridevi, 57 Devi forms, Dashavatar, Devas/Adityas/Vasus/Navagraha, Ramayana, Mahabharata, Krishna-leela, 71 rishis/munis, rakshasas & asuras, nagas, apsaras, gandharvas, kings & legends, soldiers/villagers) |
| animals & birds | **69** animals/serpents/fish (Airavata, Nandi, Kamadhenu, Uchchaihshravas, Sheshnaag…) + **48** birds (Garuda, Jatayu, hamsa, peacock, owl…) |
| environments | **110** (27 locales × dawn/day/dusk/night/fire/divine/storm/cosmic/snow): palace darbar, Ashok Vatika, banana forest, ashram, yagya-shala, Kailash, Kshirsagar, Swarga, Patala, Lanka, Ram Setu, Kurukshetra, war camp, ghats, Vrindavan, Dwarka, temple, shmashan, cosmos, theatre stage, shadow screen… |
| acting | 40+ puppet actions: walk, run, talk, point, bless, namaste, bow, raise, strike, shoot arrow, fight, fly, hover, jump, fall, appear, vanish, grow, turn, dance, meditate, spin chakra… |
| text & voice | Hindi neural TTS (edge-tts) with word boundaries, or align your own recordings; karaoke / keyword / pop subtitles; shloka cards with word glosses |
| audio | procedural raga score (16 ragas, 17 moods), 54 SFX + ambience beds, auto SFX, ducking, −14 LUFS loudnorm, stems |
| look | in-engine grade presets (+ .cube LUT export), film grain/flicker finish, 16:9 / 9:16 / 1:1 / 4:5 / 4K |

**Quick start**

```bash
pip install -r .claude/skills/mythic-25d/requirements.txt      # + ffmpeg (with libass) on PATH
python .claude/skills/mythic-25d/mythic.py doctor
python .claude/skills/mythic-25d/mythic.py make mythic_projects/demo_hanuman_bhima --quality preview
```

Then open Claude Code here and paste a prompt from `.claude/skills/mythic-25d/STARTER_PROMPT.md` (or type `/mythic-25d`).
Docs: `.claude/skills/mythic-25d/SKILL.md` and `references/`. Sample galleries: `.claude/skills/mythic-25d/docs/`.

---

# Sample Hardhat Project

This project demonstrates a basic Hardhat use case. It comes with a sample contract, a test for that contract, and a Hardhat Ignition module that deploys that contract.

Try running some of the following tasks:

```shell
npx hardhat help
npx hardhat test
REPORT_GAS=true npx hardhat test
npx hardhat node
npx hardhat ignition deploy ./ignition/modules/Lock.js
```
