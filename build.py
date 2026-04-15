"""Build tenant-research.skill (zip archive) from the tenant-research/ source.

Output zip layout matches what the Claude skills plugin expects:

    tenant-research/SKILL.md
    tenant-research/scripts/charts.py
    tenant-research/scripts/logos.py

Usage:
    python build.py [--output PATH]

Default output is ./tenant-research.skill in the repo root.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = REPO_ROOT / "tenant-research"


def build(output: Path) -> None:
    if not SOURCE_DIR.is_dir():
        sys.exit(f"error: source dir not found: {SOURCE_DIR}")

    files = sorted(p for p in SOURCE_DIR.rglob("*") if p.is_file())
    if not files:
        sys.exit(f"error: no files found under {SOURCE_DIR}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arcname = path.relative_to(REPO_ROOT).as_posix()
            zf.write(path, arcname)
            print(f"  + {arcname}")

    size_kb = output.stat().st_size / 1024
    print(f"\nbuilt {output} ({size_kb:.1f} KB, {len(files)} files)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "tenant-research.skill",
        help="output path for the .skill zip (default: ./tenant-research.skill)",
    )
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()
