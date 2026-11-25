# Mythic 2.5D skill — install / इंस्टॉल

## 1. Requirements / ज़रूरतें
- **Python 3.9+**  (Windows: python.org installer, "Add to PATH" ✔)
- **ffmpeg with libass** — Windows: `winget install Gyan.FFmpeg` · macOS: `brew install ffmpeg` · Linux: `sudo apt install ffmpeg`
- **Claude Code** (CLI / desktop / VS Code)

## 2. Put the skill where Claude Code finds it / स्किल को सही जगह रखें
Unzip, then copy the folder `mythic-25d` to **one** of:
- this project only: `<your-project>/.claude/skills/mythic-25d/`
- all projects (personal): `~/.claude/skills/mythic-25d/`  (Windows: `C:\Users\<you>\.claude\skills\mythic-25d\`)

## 3. Python packages / पैकेज
```bash
pip install -r ~/.claude/skills/mythic-25d/requirements.txt      # or the project path
python ~/.claude/skills/mythic-25d/mythic.py doctor               # everything should be ✔
```

## 4. Try the demo / डेमो चलाएँ
Copy `mythic_projects/` from the zip into your project folder, then:
```bash
python ~/.claude/skills/mythic-25d/mythic.py make mythic_projects/demo_hanuman_bhima --quality preview
# real Hindi voice (needs internet):
python ~/.claude/skills/mythic-25d/mythic.py voice mythic_projects/demo_hanuman_bhima --force
python ~/.claude/skills/mythic-25d/mythic.py make mythic_projects/demo_hanuman_bhima --quality final
```
Output: `mythic_projects/demo_hanuman_bhima/out/…_final.mp4` + `review/index.html`.

## 5. Use it with Claude / Claude के साथ
Open Claude Code in your project and paste a prompt from `STARTER_PROMPT.md` (Hindi or English),
or just type: `/mythic-25d` + your Hindi script.

Speed: preview ≈ 1–1.5 min per minute of film on 4 cores; final 1080p ≈ 6–9 min per minute.
Problems → `references/troubleshooting.md`.
