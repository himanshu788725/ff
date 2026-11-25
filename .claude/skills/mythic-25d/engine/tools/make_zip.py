"""Package the skill + demo into a single distributable zip.

    python .claude/skills/mythic-25d/engine/tools/make_zip.py [--out dist/mythic-25d-skill.zip]
"""
import argparse
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]          # .../.claude/skills/mythic-25d
REPO = SKILL.parents[2]
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIX = {".pyc", ".pyo"}

README_FIRST = """# Mythic 2.5D — painted puppet-theatre film skill for Claude Code

हिंदी: इस zip में पूरी Claude Code skill है — 602 पात्र, 117 पशु-पक्षी, 110 दृश्य, reference जैसा कैमरा,
ज़िंदा background, हिंदी आवाज़ + word-timed subtitles, संगीत, SFX, mix, grading, review.
इंस्टॉल: `mythic-25d/INSTALL.md` पढ़ें। Claude को कैसे बोलें: `mythic-25d/STARTER_PROMPT.md`।

English: the complete Claude Code skill. Install: `mythic-25d/INSTALL.md`. Prompts: `mythic-25d/STARTER_PROMPT.md`.

Contents
- `mythic-25d/`            → copy to `~/.claude/skills/mythic-25d/` (or `<project>/.claude/skills/mythic-25d/`)
- `mythic_projects/demo_hanuman_bhima/storyboard.yaml` → a full 7-shot demo to render
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "dist" / "mythic-25d-skill.zip"))
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("README_FIRST.md", README_FIRST)
        for p in sorted(SKILL.rglob("*")):
            if p.is_dir() or any(part in SKIP_DIRS for part in p.parts) or p.suffix in SKIP_SUFFIX:
                continue
            z.write(p, Path("mythic-25d") / p.relative_to(SKILL))
            n += 1
        demo = REPO / "mythic_projects" / "demo_hanuman_bhima"
        for name in ("storyboard.yaml", "script.txt"):
            if (demo / name).exists():
                z.write(demo / name, Path("mythic_projects/demo_hanuman_bhima") / name)
                n += 1
        z.writestr("mythic_projects/demo_hanuman_bhima/sfx/README.txt",
                   "Drop real SFX here named like the cue (e.g. horse_neigh.wav) to replace synthetic ones.\n")
    print(f"wrote {out} ({n} files, {out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
