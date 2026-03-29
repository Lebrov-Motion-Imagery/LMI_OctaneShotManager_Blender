#!/usr/bin/env python3
"""Build a direct-install Blender add-on zip from the addon package folder."""

from __future__ import annotations

import ast
from pathlib import Path
import zipfile


REPO_ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = REPO_ROOT / "LMI_OctaneShotManager_Blender"
DIST_DIR = REPO_ROOT / "dist"
EXCLUDED_NAMES = {".DS_Store", "AGENTS.md"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_DIRS = {"__pycache__"}


def read_version() -> str:
    init_path = ADDON_DIR / "__init__.py"
    module = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))

    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "bl_info":
                    bl_info = ast.literal_eval(node.value)
                    version = bl_info["version"]
                    return ".".join(str(part) for part in version)

    raise RuntimeError("Unable to find bl_info['version'] in __init__.py")


def iter_addon_files():
    for path in sorted(ADDON_DIR.rglob("*")):
        if path.is_dir():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield path


def build_zip() -> Path:
    version = read_version()
    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / f"LMI_OctaneShotManager_Blender-v{version}-blender-addon.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in iter_addon_files():
            archive_path = file_path.relative_to(REPO_ROOT)
            archive.write(file_path, archive_path.as_posix())

    return zip_path


def validate_zip(zip_path: Path) -> None:
    addon_root = f"{ADDON_DIR.name}/"
    expected_init = f"{ADDON_DIR.name}/__init__.py"

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if not names:
            raise RuntimeError("Built zip is empty")
        if not all(name.startswith(addon_root) for name in names):
            raise RuntimeError("Zip contains files outside the addon root folder")
        if expected_init not in names:
            raise RuntimeError("Zip is missing the addon __init__.py entry")


def main() -> None:
    zip_path = build_zip()
    validate_zip(zip_path)
    print(zip_path)


if __name__ == "__main__":
    main()
