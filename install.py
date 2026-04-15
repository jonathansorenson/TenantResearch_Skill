"""Install the local tenant-research/ source into the Claude skills-plugin dir.

Copies SKILL.md and scripts/ into the live plugin folder so edits in this repo
take effect immediately for the running Claude Code session. No restart needed.

Usage:
    python install.py [--install-dir PATH] [--dry-run]

Auto-detects the install dir on Windows. Pass --install-dir to override on
other platforms or for non-default Claude installs.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = REPO_ROOT / "tenant-research"


def find_install_dir() -> Path | None:
    """Auto-detect the skills-plugin install dir for tenant-research.

    Looks under %APPDATA%\\Claude\\local-agent-mode-sessions\\skills-plugin\\
    for any session containing skills/tenant-research/.
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    plugin_root = Path(appdata) / "Claude" / "local-agent-mode-sessions" / "skills-plugin"
    if not plugin_root.is_dir():
        return None

    candidates = list(plugin_root.glob("*/*/skills/tenant-research"))
    if not candidates:
        return None
    # If multiple sessions exist, pick the most recently modified one.
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def install(install_dir: Path, dry_run: bool) -> None:
    if not SOURCE_DIR.is_dir():
        sys.exit(f"error: source dir not found: {SOURCE_DIR}")
    if not install_dir.is_dir():
        sys.exit(
            f"error: install dir not found: {install_dir}\n"
            "Pass --install-dir to override, or install the skill via the "
            "Claude UI first to create the plugin folder."
        )

    files = sorted(p for p in SOURCE_DIR.rglob("*") if p.is_file())
    print(f"source : {SOURCE_DIR}")
    print(f"target : {install_dir}")
    print(f"files  : {len(files)}\n")

    for src in files:
        rel = src.relative_to(SOURCE_DIR)
        dst = install_dir / rel
        action = "would copy" if dry_run else "copying"
        print(f"  {action}: {rel.as_posix()}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    if dry_run:
        print("\ndry run — no files written")
    else:
        print("\ninstalled. Edits are live in the running Claude session.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=None,
        help="override the auto-detected install dir",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be copied without writing",
    )
    args = parser.parse_args()

    install_dir = args.install_dir or find_install_dir()
    if install_dir is None:
        sys.exit(
            "error: could not auto-detect Claude skills-plugin install dir.\n"
            "Pass --install-dir <path> explicitly."
        )
    install(install_dir.resolve(), args.dry_run)


if __name__ == "__main__":
    main()
