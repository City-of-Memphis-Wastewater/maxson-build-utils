# src/maxson_build_utils/macos_dmg.py
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pyhabitat
import logging

logger=logging.getLogger(__name__)


from ..state import get_pyinstaller_onedir_export_entrypoint_path 
from ..core.know_target import (
    DMG_DIST_DIR,
    get_pyproject
)
from ..helpers import PyinsMode

def purge_raw_unix_structure_from_macos_build(executable_descriptor: str, mode: PyinsMode) -> None:
    """Unused as far as i can tell. Removes duplicate CLI directories created by PyInstaller next to .app bundles."""
    if pyhabitat.on_macos() and mode == PyinsMode.ONEDIR:
        duplicate_cli_dir = Path("dist") / executable_descriptor
        if duplicate_cli_dir.exists() and duplicate_cli_dir.is_dir():
            print(f"Cleaning up duplicate raw Unix folder: {duplicate_cli_dir.resolve()}")
            shutil.rmtree(duplicate_cli_dir)


def build_macos_dmg(
    app: Path | None = None,
    app_pretty_name: str | None = None,
    version: str | None = None,
    output_dir: Path = DMG_DIST_DIR,
) -> Path:
    """Packages a macOS .app bundle into a .dmg using create-dmg."""
    print("build_macos_dmg()")
    
    if app is None:
        app = get_pyinstaller_onedir_export_entrypoint_path()

    if app.suffix != ".app":
        raise ValueError(f"Expected a .app bundle, got {app}")

    if app_pretty_name is None or version is None:
        project = get_pyproject()
        app_pretty_name = app_pretty_name or project.pretty_name
        version = version or project.version

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

