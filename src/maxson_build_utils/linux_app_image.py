#!/usr/bin/env python3
# maxson_build_utils/build_utils.py

"""Build utilities for packaging PyInstaller outputs across target platforms."""

from __future__ import annotations

from enum import Enum
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import pyhabitat

from .build_executable import run_build_executable
from .helpers import PyinsMode, IconFileType, resolve_icon_filetype, form_dynamic_name

logger = logging.getLogger(__name__)

def build_linux_appimage(
    app_dir_path: Path,
    src_folder_name: str, 
    version: str,
    app_name_pretty: str,
    icon_src: Path,
) -> Path:
    """Packages a PyInstaller ONEDIR bundle into a standalone Linux AppImage."""
    if not app_dir_path.exists():
        raise FileNotFoundError(
            f"Build directory '{app_dir_path}' does not exist.\n"
            f"Run 'maxson-build-utils build-executable --mode onedir' before calling build-appimage."
        )

    executable_descriptor = form_dynamic_name(pkg_name=src_folder_name, version=version, mode=PyinsMode.ONEDIR)

    logger.info("Executing build_linux_appimage()")
    logger.info("Source AppDir components from: %s", app_dir_path)

    if shutil.which("appimagetool") is None:
        raise RuntimeError(
            "appimagetool is not installed. Please download it or install via your package manager."
        )

    appimage_dir = Path("dist/appimage")
    appimage_dir.mkdir(parents=True, exist_ok=True)
    appimage_output_path = appimage_dir / f"{executable_descriptor}-x86_64.AppImage"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        staged_appdir = tmp_dir / f"{executable_descriptor}.AppDir"
        staged_appdir.mkdir(parents=True, exist_ok=True)

        # 1. Populate the usr/bin directory with the PyInstaller bundle
        usr_bin = staged_appdir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        shutil.copytree(app_dir_path, usr_bin / dynamic_exe_name)

        # 2. Create the AppRun entrypoint script
        apprun_path = staged_appdir / "AppRun"
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
Name={app_name_pretty}
Exec=AppRun
Icon={dynamic_exe_name}
Categories=Utility;
Terminal=true
"""
        desktop_path.write_text(desktop_content, encoding="utf-8")

        # 4. Copy and stage the icon asset
        icon_filetype = resolve_icon_filetype(icon_src)
        if icon_filetype is None:
            raise ValueError(
                f"Unsupported icon type: '{icon_src.suffix}'. "
                f"Supported types: {[x.value for x in IconFileType]}"
            )

        icon_dst = staged_appdir / f"{dynamic_exe_name}.{icon_filetype.value}"

        logger.info("Staging Linux AppImage icon: %s -> %s", icon_src.name, icon_dst.name)
        if icon_src.exists():
            shutil.copy2(icon_src, icon_dst)
        else:
            raise FileNotFoundError(
                f"Critical asset missing! Could not locate icon at: {icon_src.resolve()}"
            )

        # 5. Run appimagetool
        logger.info("Compiling AppImage to %s...", appimage_output_path)
        subprocess.run(
            [
                "appimagetool",
                str(staged_appdir.resolve()),
                str(appimage_output_path.resolve()),
            ],
            check=True,
            env=os.environ.copy(),
        )

    return appimage_output_path


def post_process_linux_build(
    app_path: Path,
    dynamic_exe_name: str,
    app_name_pretty: str,
    icon_src: Path,
    mode: PyinsMode,
) -> Path | None:
    """Handles downstream staging tasks on Linux platforms (skips Termux)."""
    is_linux = getattr(pyhabitat, "on_linux", lambda: sys.platform.startswith("linux"))()
    is_termux = getattr(pyhabitat, "on_termux", lambda: False)()

    if is_linux and not is_termux and mode == PyinsMode.ONEDIR:
        bundle_dir = app_path.parent
        return build_linux_appimage(
            app_dir_path=bundle_dir,
            dynamic_exe_name=dynamic_exe_name,
            app_name_pretty=app_name_pretty,
            icon_src=icon_src,
        )

    return None