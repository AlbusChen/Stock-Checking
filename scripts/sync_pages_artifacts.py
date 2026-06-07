#!/usr/bin/env python3
"""Copy the latest Vite build to repo root for branch-based GitHub Pages."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def replace_path(source: Path, target: Path) -> None:
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def main() -> None:
    required = [DIST / "index.html", DIST / "assets", DIST / "data"]
    missing = [path for path in required if not path.exists()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise SystemExit(f"Missing build artifacts: {names}")

    replace_path(DIST / "index.html", ROOT / "index.html")
    replace_path(DIST / "assets", ROOT / "assets")
    replace_path(DIST / "data", ROOT / "data")
    print("Synced dist/index.html, dist/assets, and dist/data to repo root")


if __name__ == "__main__":
    main()
