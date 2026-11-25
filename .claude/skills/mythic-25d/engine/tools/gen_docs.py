"""Regenerate references/catalog-index.md and references/environments.md from the engine."""
import sys
from collections import OrderedDict
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
from mythic25d.catalog import all_entities  # noqa: E402
from mythic25d.envs import LIFE, LOCALES, list_envs  # noqa: E402
from mythic25d.props import PROPS, HANGING  # noqa: E402
from mythic25d.actions import ACTION_HELP  # noqa: E402
from mythic25d.music import MOODS, RAGAS  # noqa: E402
from mythic25d.sfx import GEN  # noqa: E402
from mythic25d.grade import GRADES  # noqa: E402

REF = ENGINE.parent / "references"
es = all_entities()
groups = OrderedDict()
for e in es.values():
    groups.setdefault((e.get("kind", "humanoid"), e.get("cat", "?")), []).append(e)
lines = ["# Catalog index (auto-generated — `python engine/tools/gen_docs.py`)", "",
         f"**{len(es)} entities**: " + ", ".join(f"{k}: {sum(1 for e in es.values() if e.get('kind', 'humanoid') == k)}"
                                              for k in ("humanoid", "quadruped", "serpent", "fish", "bird")), "",
         "Use the `id` in storyboards (`who: hanuman`). Override any look per shot or in the storyboard `characters:` "
         "section: `{base: bhima, dhoti: [maroon, dots, gold], scale: 1.1}`.", ""]
for (kind, cat), lst in groups.items():
    lines.append(f"## {cat} · {kind} ({len(lst)})")
    lines.append("")
    lines.append(" · ".join(f"`{e['id']}` {e.get('hi', '')}" for e in lst))
    lines.append("")
(REF / "catalog-index.md").write_text("\n".join(lines), encoding="utf-8")

L = ["# Environments, props, actions, moods (auto-generated)", "",
     f"## {len(list_envs())} environments  (`env: <locale>_<time>`)", "",
     "Times: dawn · day · dusk · night · fire · divine · storm · cosmic · snow (each locale lists the ones it supports).", "",
     "| locale | times | what it is |", "|---|---|---|"]
for loc, (_, times, desc) in LOCALES.items():
    L.append(f"| `{loc}` | {', '.join(times)} | {desc} |")
L += ["", "## Living background — automatic ambient creatures per locale", "",
      "| locale | creatures (mode, when) |", "|---|---|"]
for loc, items in LIFE.items():
    if items:
        L.append(f"| `{loc}` | " + ", ".join(f"{w} ({m}{', ' + '/'.join(t) if t else ''})" for w, m, kw, t in items) + " |")
L += ["", "All natural sets also get wind-animated trees/grass/flowers, drifting clouds and foreground foliage.",
      "Override per shot with `life:` (list) or `life: false`."]
L += ["", "## Props (`props:` in a shot)", "",
      ", ".join(f"`{k}`" + (" (hangs)" if k in HANGING else "") for k in PROPS), "",
      "## Actions (`actions:` on a cast member)", "", "| action | params |", "|---|---|"]
L += [f"| `{k}` | {v} |" for k, v in ACTION_HELP.items()]
L += ["", "## Music moods", "", "| mood | raga | bpm | lead | percussion |", "|---|---|---|---|---|"]
L += [f"| `{k}` | {v[0]} | {v[1]} | {v[2]} | {v[3]} |" for k, v in MOODS.items()]
L += ["", "Ragas: " + ", ".join(f"`{r}`" for r in RAGAS), "", "## SFX names", "", ", ".join(f"`{k}`" for k in sorted(GEN)), "",
      "## Grades", ""] + [f"- `{k}` — {v['desc']}" for k, v in GRADES.items()]
(REF / "environments.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", REF / "catalog-index.md", "and", REF / "environments.md")
