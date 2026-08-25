"""Build script to assemble an AppDir and compile it into an AppImage."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import pyhabitat

APP_NAME = "maxson-build-utils"
APP_ID = "io.github.city_of_memphis_wastewater.maxson-build-utils"
IMPORT_NAME = "maxson_build_utils"


def build_appimage() -> Path:
    if shutil.which("appimagetool") is None:
        raise RuntimeError(
            "appimagetool is not installed. Please download it or install via your package manager."
        )

    root_dir = Path(__file__).resolve().parents[2]
    pyinstaller_dist = root_dir / "dist" / "pyinstaller" / APP_NAME

    if not pyinstaller_dist.exists():
        raise FileNotFoundError(
            f"PyInstaller build directory '{pyinstaller_dist}' does not exist.\n"
            f"Build the PyInstaller onedir distribution first."
        )

    out_dir = root_dir / "dist" / "appimage"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        appdir = Path(tmp) / f"{APP_NAME}.AppDir"
        appdir.mkdir(parents=True, exist_ok=True)

        # 1. Populate usr/bin with the PyInstaller distribution content
        usr_bin = appdir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)

        # Copy the contents of onedir into usr/bin directly (or subfolder with launcher symlink)
        shutil.copytree(pyinstaller_dist, usr_bin, dirs_exist_ok=True)

        # Ensure main binary is executable
        main_bin = usr_bin / APP_NAME
        if main_bin.exists():
            main_bin.chmod(0o755)

        # 2. Deploy AppRun
        apprun_dst = appdir / "AppRun"
        shutil.copy2(root_dir / "packaging" / "appimage" / "AppRun", apprun_dst)
        apprun_dst.chmod(0o755)

        # 3. Deploy Desktop file
        desktop_src = root_dir / "packaging" / "appimage" / f"{APP_ID}.desktop"
        shutil.copy2(desktop_src, appdir / f"{APP_ID}.desktop")

        # 4. Deploy Icon
        icon_src = root_dir / "src" / IMPORT_NAME / "data" / "icons" / "placeholder.svg"
        if not icon_src.exists():
            icon_src = root_dir / "src" / IMPORT_NAME / "data" / "icons" / "placeholder.png"

        if icon_src.exists():
            icon_ext = icon_src.suffix
            icon_dst = appdir / f"{APP_ID}{icon_ext}"
            shutil.copy2(icon_src, icon_dst)
            # Create root .DirIcon symlink for AppImage standard compliance
            (appdir / ".DirIcon").symlink_to(icon_dst.name)

        # 5. Execute appimagetool
        # Pass the dynamic architecture directly to appimagetool environment

        system = pyhabitat.SystemInfo()

        arch = system.get_arch()
        appimage_output = out_dir / f"{APP_NAME}-{arch}.AppImage"

        env = os.environ.copy()
        env["ARCH"] = arch

        subprocess.run(
            ["appimagetool", str(appdir), str(appimage_output)],
            check=True,
            env=env,
        )

    return appimage_output


if __name__ == "__main__":
    build_appimage()
