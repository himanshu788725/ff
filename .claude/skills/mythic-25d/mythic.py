#!/usr/bin/env python3
"""Launcher for the mythic25d engine (works from any directory)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine"))
from mythic25d.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
