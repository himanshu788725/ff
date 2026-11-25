"""Catalog: characters / animals / birds (JSON) + project-level custom entries.

who can be:
  "hanuman"                         -> catalog entry
  {"base": "bhima", "dhoti": [...]} -> catalog entry with overrides
  {"kind": "humanoid", ...}         -> fully custom spec
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from .util import DATA_DIR

_EXTRA: dict = {}


@lru_cache(maxsize=1)
def _load():
    db = {}
    for name in ("characters", "animals", "birds"):
        p = DATA_DIR / f"{name}.json"
        if p.exists():
            for e in json.loads(p.read_text(encoding="utf-8")):
                db[e["id"]] = e
    # user/project extensions via env var (path list)
    for extra in filter(None, os.environ.get("MYTHIC_EXTRA_CATALOG", "").split(os.pathsep)):
        try:
            for e in json.loads(Path(extra).read_text(encoding="utf-8")):
                db[e["id"]] = e
        except Exception as ex:  # pragma: no cover
            print(f"[catalog] could not load {extra}: {ex}")
    return db


def register(entries: dict | list):
    """Register project-defined characters (storyboard `characters:` section)."""
    if isinstance(entries, dict):
        entries = [dict(v, id=k) for k, v in entries.items()]
    for e in entries:
        _EXTRA[e["id"]] = e


def all_entities():
    d = dict(_load())
    d.update(_EXTRA)
    return d


def get_entity(who) -> dict:
    db = all_entities()
    if isinstance(who, dict):
        base_id = who.get("base")
        spec = dict(db.get(base_id, {})) if base_id else {}
        if base_id and not spec:
            raise KeyError(f"unknown base character '{base_id}'")
        spec.update({k: v for k, v in who.items() if k != "base"})
        if "kind" not in spec:
            spec["kind"] = "humanoid"
        spec.setdefault("id", base_id or "custom")
        if spec["kind"] in ("quadruped", "bird") and base_id and "base" in db.get(base_id, {}):
            spec["base"] = db[base_id]["base"]
        return spec
    if who in db:
        e = dict(db[who])
        if e.get("kind") in ("quadruped", "bird") and e.get("base"):
            pass
        return e
    raise KeyError(f"unknown character/animal '{who}'. Try: mythic.py search {who}")


def search(q: str, limit=40):
    q = q.lower().strip()
    out = []
    for e in all_entities().values():
        hay = " ".join(str(e.get(k, "")) for k in ("id", "hi", "en", "cat", "kind")).lower()
        if q in hay:
            out.append(e)
    out.sort(key=lambda e: (not e["id"].startswith(q), e["id"]))
    return out[:limit]
