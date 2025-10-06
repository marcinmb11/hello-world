#!/usr/bin/env python3
"""Create a distributable archive with all assets required to run the app."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
DEFAULT_BUNDLE_NAME = "finance_app_bundle"

FILES_TO_INCLUDE = [
    ROOT / "README.md",
    ROOT / "requirements.txt",
    ROOT / "app.py",
    ROOT / "example_usage.py",
]
DIRECTORIES_TO_INCLUDE = [
    ROOT / "finance_app",
    ROOT / "templates",
    ROOT / "static",
    ROOT / "scripts",
    ROOT / "images",
]
IGNORE_DIR_NAMES = {"__pycache__", ".git", ".venv", "dist"}
IGNORE_FILE_SUFFIXES = {".pyc", ".pyo", ".pyd"}
IGNORE_FILE_NAMES = {".DS_Store"}


def should_skip(path: Path) -> bool:
    if any(part in IGNORE_DIR_NAMES for part in path.parts):
        return True
    if path.suffix in IGNORE_FILE_SUFFIXES:
        return True
    if path.name in IGNORE_FILE_NAMES:
        return True
    return False


def iter_directory(directory: Path) -> Iterable[Path]:
    for item in directory.rglob("*"):
        if should_skip(item):
            continue
        if item.is_dir():
            continue
        yield item


def build_bundle(name: str, overwrite: bool) -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    bundle_path = DIST_DIR / f"{name}.zip"

    if bundle_path.exists():
        if overwrite:
            bundle_path.unlink()
        else:
            raise SystemExit(
                f"Bundle {bundle_path.name} already exists. Use --overwrite to replace it."
            )

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in FILES_TO_INCLUDE:
            if not file_path.exists():
                continue
            archive.write(file_path, file_path.relative_to(ROOT))
        for directory in DIRECTORIES_TO_INCLUDE:
            if not directory.exists():
                continue
            for item in iter_directory(directory):
                archive.write(item, item.relative_to(ROOT))

    return bundle_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the finance toolkit into a downloadable archive."
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_BUNDLE_NAME,
        help="Base name for the generated archive (without extension).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing archive with the same name.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle_path = build_bundle(args.name, args.overwrite)
    print(f"Created bundle at {bundle_path}")
    print("You can distribute the zip file and run the application after extracting it.")


if __name__ == "__main__":
    main()
