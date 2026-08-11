#!/usr/bin/env python3
# maxson_build_utils/build_utils.py

"""Build utilities for packaging PyInstaller outputs across target platforms."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import pyhabitat

from .helpers import PyinsMode, IconFileType, resolve_icon_filetype
from .state import get_pyinstaller_onedir_build_dir, get_pyinstaller_onedir_exe_filename

logger = logging.getLogger(__name__)

def build_linux_appimage(
    app_name_pretty: str, # for metadata
    icon_src: Path,
    app_dir_path: Path | str | None = None, # pyinstaller_onedir_build_dir
    app_filename: str | None = None, # pyinstaller produced executable filename
) -> Path:
    """Packages a PyInstaller ONEDIR bundle into a standalone Linux AppImage. This assume it has already been build and that strings were written to the dworshak config file as state."""


    if app_dir_path is None:
        app_dir_path = get_pyinstaller_onedir_build_dir()

    if app_filename is None:
        app_filename = get_pyinstaller_onedir_exe_filename()

    if not app_dir_path.exists():
        raise FileNotFoundError(
            f"Build directory '{app_dir_path}' does not exist.\n"
            f"Run package's expection 'build_executable.py' script first."
        )

    executable_descriptor = app_filename.stem
    logger.info("Executing build_linux_appimage()")
    logger.info("Source AppDir components from: %s", app_dir_path)

    if shutil.which("appimagetool") is None:
        raise RuntimeError(
            "appimagetool is not installed. Please download it or install via your package manager."
        )

    appimage_dir = Path("dist/appimage")
    appimage_dir.mkdir(parents=True, exist_ok=True)
    appimage_output_path = appimage_dir / f"{executable_descriptor}.AppImage"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        staged_appdir = tmp_dir / f"{executable_descriptor}.AppDir"
        staged_appdir.mkdir(parents=True, exist_ok=True)

        # 1. Populate the usr/bin directory with the PyInstaller bundle
        usr_bin = staged_appdir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        shutil.copytree(app_dir_path, usr_bin / executable_descriptor) # assumed to exist, this had better use the same filename from the pyinstaller bundle

        # 2. Create the AppRun entrypoint script
        apprun_path = staged_appdir / "AppRun"
        apprun_content = f"""#!/bin/sh
HERE="$(dirname "$(readlink -f "${{0}}")")"
EXEC="${{HERE}}/usr/bin/{executable_descriptor}/{executable_descriptor}"
exec "${{EXEC}}" "$@"
"""
        apprun_path.write_text(apprun_content, encoding="utf-8")
        apprun_path.chmod(0o755)

        # 3. Create the .desktop file
        desktop_path = staged_appdir / f"{executable_descriptor}.desktop"
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name_pretty}
Exec=AppRun
Icon={executable_descriptor}
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

        icon_dst = staged_appdir / f"{executable_descriptor}.{icon_filetype.value}"

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
    executable_descriptor: str,
    app_name_pretty: str,
    icon_src: Path,
    mode: PyinsMode,
) -> Path | None:
    """Defunct. Handles downstream staging tasks on Linux platforms (skips Termux)."""
    is_linux = getattr(pyhabitat, "on_linux", lambda: sys.platform.startswith("linux"))()
    is_termux = getattr(pyhabitat, "on_termux", lambda: False)()

    if is_linux and not is_termux and mode == PyinsMode.ONEDIR:
        bundle_dir = app_path.parent
        return build_linux_appimage(
            app_dir_path=bundle_dir,
            executable_descriptor=executable_descriptor,
            app_name_pretty=app_name_pretty,
            icon_src=icon_src,
        )

    return None

# example use case of post_process:
"""
app_path, app_filename = run_pyinstaller(
            executable_descriptor=executable_descriptor,
            main_script_path=cli_main_file,
            src_folder_name=src_folder_name,
            mode=mode,
            is_windowed_build=is_windowed_build,
            icon_ico_path=icon_ico_path,
            icon_icns_path=icon_icns_path,
            collect_data_pkgs=collect_data_pkgs,
            collect_binary_pkgs=collect_binary_pkgs,
        )

if icon_png_path and icon_png_path.exists():
    appimage_path = post_process_linux_build(
        app_path=app_path,
        executable_descriptor=executable_descriptor,
        app_name_pretty=app_name_pretty,
        icon_src=icon_png_path,
        mode=mode,
    )
    if appimage_path:
        logger.info("AppImage successfully generated at: %s", appimage_path)
"""