# Troubleshooting

Run `mythic.py doctor` first — it checks ffmpeg/ffprobe, libass + HarfBuzz, fonts, Pillow raqm, numpy/yaml,
edge-tts, faster-whisper.

| symptom | cause | fix |
|---|---|---|
| `ffmpeg not found` | ffmpeg missing | Windows: `winget install Gyan.FFmpeg` (full build) · macOS: `brew install ffmpeg` · Linux: `sudo apt install ffmpeg` |
| Hindi shows ◌ dotted circles / broken matras | letter spacing in ASS, or ffmpeg/libass without HarfBuzz | keep style Spacing = 0 (default); use a full ffmpeg build (gyan.dev "full", Homebrew, Ubuntu ≥ 22.04) |
| Hindi shows boxes □ | font not found by libass | fonts must be in `engine/mythic25d/fonts/` (passed via `fontsdir`); don't rename the font families in the ASS |
| `No module named yaml/numpy/PIL` | deps | `pip install -r <SKILL_DIR>/requirements.txt` (Python ≥ 3.9) |
| `edge-tts failed … Cannot connect` | no internet / firewall / proxy blocks `speech.platform.bing.com` | connect & `mythic.py voice <proj> --force`; or record your own VO (`engine: files`); or `engine: none` for silent previews |
| `edge-tts … 403` | old edge-tts | `pip install -U edge-tts` |
| subtitles out of sync with own recording | leading silence / noisy audio | trim silence, `pip install faster-whisper`, re-run `voice --force` |
| render very slow | final 1080p on few cores | iterate with `--quality preview` (half-res) or `draft`; `--shots` for a few shots; `--workers N`; close other apps |
| `MemoryError` / machine freezes | too many workers at 4K | `--workers 2`, or 1080p |
| puppets look blurry at close-ups | camera zoom > 1.3 or scale > 1.4 | engine picks sprite resolution automatically up to 22 px/unit; reduce zoom or scale |
| character cut at top | crowns are tall | lower `scale`, use `pull_out`, or set camera `y: [0.46, 0.46]` |
| puppet doesn't talk | line `who` ≠ cast `id` | give the cast entry `id:` equal to the speaker |
| unknown env / character | typo / not in catalog | `mythic.py list envs`, `mythic.py search <name>` — or define it under `characters:` |
| a stale look after editing engine code | cache | caches key on source hashes; to force: delete `~/.cache/mythic25d` (or `MYTHIC_CACHE`) |
| black flashes between shots | `transition: dip` | use `crossfade` |
| audio too quiet/loud | loudness target | `mythic.py mix <proj> --lufs -14` (YouTube) |
| music fights the narration | bed too loud | `music.volume_db: -20` |
| Windows: path errors in ffmpeg `ass=` | drive colon escaping | run from the project drive; paths are escaped automatically — avoid `'` in folder names |
| final has no audio | mix missing | run `mythic.py mix <proj>` before `master` (or use `make`) |

Where things are:
- engine code `engine/mythic25d/` · catalog JSON `engine/mythic25d/data/` · fonts `engine/mythic25d/fonts/`
- caches `~/.cache/mythic25d/{rigs,props,envs}` · project outputs `mythic_projects/<name>/{audio,build,subs,out,review}`

Reporting a bug to Claude: include the command, the last 20 lines of output, and `review/qa.json`.
