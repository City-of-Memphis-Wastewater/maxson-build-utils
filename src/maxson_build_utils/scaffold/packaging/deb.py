# src/maxson_build_utils/scaffold/packaging/deb.py
from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file
from ...names import to_kebab_case
from ...pyproject import MaxsonPyProject

CONTROL_TEMPLATE = """Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Maxson Developer <developer@maxson.internal>
Description: {APP_NAME} desktop application package.
 Generated automatically via maxson-build-utils.
"""

DESKTOP_TEMPLATE = """[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec=/usr/bin/{APP_NAME}
Icon={APP_NAME}
Categories=Utility;
Terminal=false
"""

BUILD_SCRIPT_TEMPLATE = '''"""Build script to assemble a filesystem root structure and package into a Debian deb file."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

APP_NAME = "{APP_NAME}"
IMPORT_NAME = "{IMPORT_NAME}"


def build_deb() -> Path:
    if shutil.which("dpkg-deb") is None:
        raise RuntimeError(
            "dpkg-deb is not installed. Debian packaging requires an Ubuntu/Debian environment."
        )

    root_dir = Path(__file__).resolve().parents
    pyinstaller_dist = root_dir / "dist" / "pyinstaller" / APP_NAME

    if not pyinstaller_dist.exists():
        raise FileNotFoundError(
            f"PyInstaller build directory '{pyinstaller_dist}' does not exist.\\n"
            f"Build the PyInstaller onedir distribution first."
        )

    out_dir = root_dir / "dist" / "deb"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Setup a clean staging space
    stage_dir = out_dir / f"{APP_NAME}_stage"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    # 2. Replicate standard Debian filesystem structure
    deb_control_dir = stage_dir / "DEBIAN"
    deb_control_dir.mkdir(parents=True, exist_ok=True)
    
    usr_bin = stage_dir / "usr" / "bin"
    usr_bin.mkdir(parents=True, exist_ok=True)
    
    usr_lib = stage_dir / "usr" / "lib" / APP_NAME
    usr_lib.mkdir(parents=True, exist_ok=True)
    
    apps_dir = stage_dir / "usr" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    
    icons_dir = stage_dir / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    icons_dir.mkdir(parents=True, exist_ok=True)

    # 3. Deploy binaries and layout elements
    shutil.copy2(root_dir / "packaging" / "deb" / "control", deb_control_dir / "control")
    shutil.copy2(root_dir / "packaging" / "deb" / f"{APP_NAME}.desktop", apps_dir / f"{APP_NAME}.desktop")
    shutil.copytree(pyinstaller_dist, usr_lib, dirs_exist_ok=True)

    # Create safe symlink launcher at /usr/bin/{APP_NAME} pointing to the library deployment
    launcher_file = usr_bin / APP_NAME
    launcher_file.write_text(f'#!/bin/sh\\nexec "/usr/lib/{APP_NAME}/{APP_NAME}" "$@"\\n', encoding="utf-8")
    launcher_file.chmod(0o755)

    # 4. Deploy standard theme icons
    src_icons_dir = root_dir / "src" / IMPORT_NAME / "data" / "icons"
    icon_src = src_icons_dir / f"{APP_NAME}.png"
    if not icon_src.exists():
        icon_src = src_icons_dir / "placeholder.png"
    if not icon_src.exists():
        icon_src = src_icons_dir / "placeholder.svg"

    if icon_src.exists():
        shutil.copy2(icon_src, icons_dir / f"{APP_NAME}{icon_src.suffix}")

    # 5. Pack deb distribution
    deb_output_path = out_dir / f"{APP_NAME}_amd64.deb"
    subprocess.run(
        ["dpkg-deb", "--build", str(stage_dir), str(deb_output_path)],
        check=True,
    )

    # Clean staging footprint
    shutil.rmtree(stage_dir)
    return deb_output_path


if __name__ == "__main__":
    build_deb()
'''


def resolve_deb_metadata(path: Path | str | None = None) -> dict[str, str]:
    pyproject = MaxsonPyProject(path)

    import_name = pyproject.import_name
    app_name = pyproject.app_name
    app_name_kebab = to_kebab_case(app_name)
    
    # Try fetching project version metadata dynamically, fallback safely
    version = pyproject.get("project", "version") or "0.1.0"

    return {
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
        "VERSION": version,
    }


def run_init_deb(root_dir: Path | str | None = None) -> list[Path]:
    """Scaffold packaging/deb/ assets and return generated file paths."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_deb_metadata(target_dir / "pyproject.toml")

    deb_dir = target_dir / "packaging" / "deb"
    deb_dir.mkdir(parents=True, exist_ok=True)

    app_name = meta["APP_NAME"]

    files_to_create = {
        deb_dir / "control": CONTROL_TEMPLATE,
        deb_dir / f"{app_name}.desktop": DESKTOP_TEMPLATE,
        deb_dir / "build_deb.py": BUILD_SCRIPT_TEMPLATE,
    }

    created_paths: list[Path] = []
    for path, template in files_to_create.items():
        write_str_to_file(path=path, text=template.format(**meta))
        created_paths.append(path)

    return created_paths
