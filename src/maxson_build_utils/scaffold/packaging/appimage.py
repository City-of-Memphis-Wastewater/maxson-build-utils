# src/maxson_build_utils/scaffold/packaging/appimage.py
from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file
from ...names import to_kebab_case
from ...pyproject import MaxsonPyProject

APPRUN_TEMPLATE = """#!/bin/sh
set -e
HERE="$(dirname "$(readlink -f "${{0}}")")"
export PATH="${{HERE}}/usr/bin:${{PATH}}"
export LD_LIBRARY_PATH="${{HERE}}/usr/lib:${{LD_LIBRARY_PATH}}"
export XDG_DATA_DIRS="${{HERE}}/usr/share:${{XDG_DATA_DIRS:-/usr/local/share:/usr/share}}"

EXEC="${{HERE}}/usr/bin/{APP_NAME}"
exec "${{EXEC}}" "$@"
"""

DESKTOP_TEMPLATE = """[Desktop Entry]
Name={APP_NAME}
Exec={APP_NAME}
Icon={APP_ID}
Type=Application
Categories=Utility;
"""

BUILD_SCRIPT_TEMPLATE = '''"""Build script to assemble an AppDir and compile it into an AppImage."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import platform

APP_NAME = "{APP_NAME}"
APP_ID = "{APP_ID}"
IMPORT_NAME = "{IMPORT_NAME}"


def build_appimage() -> Path:
    if shutil.which("appimagetool") is None:
        raise RuntimeError(
            "appimagetool is not installed. Please download it or install via your package manager."
        )

    root_dir = Path(__file__).resolve().parents[2]
    pyinstaller_dist = root_dir / "dist" / "pyinstaller" / APP_NAME

    if not pyinstaller_dist.exists():
        raise FileNotFoundError(
            f"PyInstaller build directory '{{pyinstaller_dist}}' does not exist.\\n"
            f"Build the PyInstaller onedir distribution first."
        )

    out_dir = root_dir / "dist" / "appimage"
    out_dir.mkdir(parents=True, exist_ok=True)
    appimage_output = out_dir / f"{{APP_NAME}}-x86_64.AppImage"

    with tempfile.TemporaryDirectory() as tmp:
        appdir = Path(tmp) / f"{{APP_NAME}}.AppDir"
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
        desktop_src = root_dir / "packaging" / "appimage" / f"{{APP_ID}}.desktop"
        shutil.copy2(desktop_src, appdir / f"{{APP_ID}}.desktop")

        # 4. Deploy Icon
        icon_src = root_dir / "src" / IMPORT_NAME / "data" / "icons" / "placeholder.svg"
        if not icon_src.exists():
            icon_src = root_dir / "src" / IMPORT_NAME / "data" / "icons" / "placeholder.png"

        if icon_src.exists():
            icon_ext = icon_src.suffix
            icon_dst = appdir / f"{{APP_ID}}{{icon_ext}}"
            shutil.copy2(icon_src, icon_dst)
            # Create root .DirIcon symlink for AppImage standard compliance
            (appdir / ".DirIcon").symlink_to(icon_dst.name)

        # 5. Execute appimagetool
        # Pass the dynamic architecture directly to appimagetool environment
        arch = platform.machine()
        appimage_output = out_dir / f"{{APP_NAME}}-{{arch}}.AppImage"

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
'''


def resolve_appimage_metadata(path: Path | str | None = None) -> dict[str, str]:
    pyproject = MaxsonPyProject(path)

    import_name = pyproject.import_name
    app_name = pyproject.app_name
    app_name_kebab = to_kebab_case(app_name)

    app_id = pyproject.get("tool", "maxson-build-utils", "appimage", "app-id")
    if not app_id:
        app_id = pyproject.get("tool", "maxson-build-utils", "packaging", "appimage", "app-id")

    if not app_id:
        domain = pyproject.get("tool", "maxson-build-utils", "appimage", "domain") or "io.github"
        org = pyproject.get("tool", "maxson-build-utils", "appimage", "org") or "city_of_memphis_wastewater"
        org_clean = org.replace("-", "_").replace(" ", "_").lower()
        app_id = f"{domain}.{org_clean}.{app_name_kebab}"

    return {
        "APP_ID": app_id,
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
    }


def run_init_appimage(root_dir: Path | str | None = None) -> list[Path]:
    """Scaffold packaging/appimage/ assets and return generated file paths."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_appimage_metadata(target_dir / "pyproject.toml")

    appimage_dir = target_dir / "packaging" / "appimage"
    appimage_dir.mkdir(parents=True, exist_ok=True)

    app_id = meta["APP_ID"]

    files_to_create = {
        appimage_dir / f"{app_id}.desktop": DESKTOP_TEMPLATE,
        appimage_dir / "AppRun": APPRUN_TEMPLATE,
        appimage_dir / "build_appimage.py": BUILD_SCRIPT_TEMPLATE,
    }

    created_paths: list[Path] = []
    for path, template in files_to_create.items():
        write_str_to_file(path=path, text=template.format(**meta))
        if path.name == "AppRun":
            path.chmod(0o755)
        created_paths.append(path)

    return created_paths
