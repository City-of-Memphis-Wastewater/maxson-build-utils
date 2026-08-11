# src/maxson_build_utils/macos_dmg.py
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pyhabitat

from maxson_build_utils.helpers import PyinsMode

STANDARD_MACOS_APP_DIST_DIR = Path("dist")
DIST_DIR_ONEDIR = Path("dist") / PyinsMode.ONEDIR.value


def purge_raw_unix_structure_from_macos_build(executable_descriptor: str, mode: PyinsMode) -> None:
    """Removes duplicate CLI directories created by PyInstaller next to .app bundles."""
    if pyhabitat.on_macos() and mode == PyinsMode.ONEDIR:
        duplicate_cli_dir = Path("dist") / executable_descriptor
        if duplicate_cli_dir.exists() and duplicate_cli_dir.is_dir():
            print(f"Cleaning up duplicate raw Unix folder: {duplicate_cli_dir.resolve()}")
            shutil.rmtree(duplicate_cli_dir)


def move_macos_app(macos_app_filename: str, app_path: Path) -> Path:
    """Relocates standard PyInstaller .app bundle into dist/onedir/."""
    src = STANDARD_MACOS_APP_DIST_DIR / macos_app_filename
    dst = DIST_DIR_ONEDIR / macos_app_filename
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        return dst
    return app_path


def build_macos_dmg(
    app: Path,
    app_pretty_name: str,
    version: str,
    output_dir: Path = Path("dist/upload"),
) -> Path:
    """Packages a macOS .app bundle into a .dmg using create-dmg."""
    print("build_macos_dmg()")
    print(f"{app=}")

    if app.suffix != ".app":
        raise ValueError(f"Expected a .app bundle, got {app}")

    if shutil.which("create-dmg") is None:
        raise RuntimeError("create-dmg is not installed. Install with: brew install create-dmg")

    output_dir.mkdir(parents=True, exist_ok=True)
    dmg_path = output_dir / f"{app.stem}.dmg"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        staged = tmp_path / app.name
        shutil.copytree(app, staged)

        cmd = [
            "create-dmg",
            "--volname",
            f"{app_pretty_name} {version}",
            "--window-size",
            "500",
            "300",
            "--icon-size",
            "100",
            "--icon",
            staged.name,
            "150",
            "180",
            "--app-drop-link",
            "450",
            "180",
            str(dmg_path.resolve()),
            str(tmp_path),
        ]

        print(f"Executing create-dmg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    return dmg_path


def post_process_macos_build(
    app_filename: str,
    app_path: Path,
    mode: PyinsMode,
    app_pretty_name: str,
    version: str,
) -> tuple[Path, Path | None]:
    """Coordinates post-build cleanup, app relocation, and DMG generation for macOS."""
    if pyhabitat.on_macos() and mode == PyinsMode.ONEDIR:
        app_path = move_macos_app(app_filename, app_path)
        dmg_path = build_macos_dmg(
            app=app_path,
            app_pretty_name=app_pretty_name,
            version=version,
        )
        return app_path, dmg_path
    return app_path, None
