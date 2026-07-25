#!/usr/bin/env python3 
# build_utils/build_utils.py

from __future__ import annotations
import pyhabitat
import sys
import logging
from pathlib import Path 
import shutil
import tempfile
import subprocess
import os

logger = logging.getLogger(__name__)

from copy_n_launch_xlsx.paths import (
        APP_NAME_PRETTY, get_ico_icon, get_png_icon
        )
from build_utils.build_utils import PyinsMode

def build_linux_appimage(app_dir_path: Path, dynamic_exe_name: str) -> Path:
    """
    Packages a PyInstaller ONEDIR bundle into a standalone Linux AppImage.
    """
    print("build_linux_appimage()")
    print(f"Source AppDir components from: {app_dir_path}")

    if shutil.which("appimagetool") is None:
        raise RuntimeError(
            "appimagetool is not installed. Please download it or install via your package manager."
        )

    upload_dir = Path("dist/upload")
    upload_dir.mkdir(parents=True, exist_ok=True)
    appimage_output_path = upload_dir / f"{dynamic_exe_name}-x86_64.AppImage"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        staged_appdir = tmp_dir / f"{dynamic_exe_name}.AppDir"
        staged_appdir.mkdir(parents=True, exist_ok=True)

        # 1. Populate the usr/bin directory with the PyInstaller bundle
        usr_bin = staged_appdir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        
        # If ONEDIR, app_dir_path points to the directory containing everything
        shutil.copytree(app_dir_path, usr_bin / dynamic_exe_name)

        # 2. Create the AppRun entrypoint script
        apprun_path = staged_appdir / "AppRun"
        # Points to the actual executable inside the copied folder
        apprun_content = f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
EXEC="${{HERE}}/usr/bin/{dynamic_exe_name}/{dynamic_exe_name}"
exec "${{EXEC}}" "$@"
"""
        apprun_path.write_text(apprun_content, encoding="utf-8")
        apprun_path.chmod(0o755)

        # 3. Create the .desktop file
        desktop_path = staged_appdir / f"{dynamic_exe_name}.desktop"
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME_PRETTY}
Exec=AppRun
Icon={dynamic_exe_name}
Categories=Utility;
Terminal=true
"""
        desktop_path.write_text(desktop_content, encoding="utf-8")

        # 4. Copy the icon file (assuming get_ico_icon can point to or be used as a PNG variant)
        # AppImage prefers PNG or SVG at the root named matching the Icon field in the desktop file
        icon_src = get_png_icon()  
        icon_dst = staged_appdir / f"{dynamic_exe_name}.png"

        print(f"Staging Linux AppImage icon: {icon_src.name} -> {icon_dst.name}")
        if icon_src.exists():
            shutil.copy2(icon_src, icon_dst)
        else:
            raise FileNotFoundError(f"Critical asset missing! Could not locate icon at: {icon_src.resolve()}")

        # 5. Run appimagetool
        print(f"Compiling AppImage to {appimage_output_path}...")
        subprocess.run(
            [
                "appimagetool",
                str(staged_appdir.resolve()),
                str(appimage_output_path.resolve())
            ],
            check=True,
            env=os.environ.copy() # Ensure ARCH flags or paths are preserved
        )

    return appimage_output_path


def post_process_linux_build(app_path: Path, dynamic_exe_name: str, mode: PyinsMode):
    """Handles downstream staging tasks on Linux platforms."""
    # Ensure pyhabitat has an on_linux wrapper, or fallback to sys.platform
    is_linux = getattr(pyhabitat, "on_linux", lambda: sys.platform.startswith("linux"))()
    
    if is_linux and mode == PyinsMode.ONEDIR:
        # app_path for ONEDIR points to the internal executable; 
        # we need its parent folder containing the dependency libraries
        bundle_dir = app_path.parent
        appimage_path = build_linux_appimage(bundle_dir, dynamic_exe_name)
        return appimage_path
    return None
