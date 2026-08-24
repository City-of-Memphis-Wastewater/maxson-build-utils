# src/maxson_build_utils/scaffold/packaging/deb.py
from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file
from ...names import to_kebab_case
from ...pyproject import MaxsonPyProject

CONTROL_TEMPLATE = """Package: {APP_NAME}
Version: __VERSION__
Section: utils
Priority: optional
Architecture: __ARCH__
Maintainer: City of Memphis Wastewater <support@memphistn.gov>
Description: {DESCRIPTION}
"""

DESKTOP_TEMPLATE = """[Desktop Entry]
Name={PRETTY_NAME}
Exec={APP_NAME}
Icon={APP_NAME}
Type=Application
Categories=Utility;
Terminal=false
"""

LAUNCHER_TEMPLATE = """#!/bin/bash
exec /opt/{APP_NAME}/venv/bin/{APP_NAME} "$@"
"""


def resolve_deb_metadata(path: Path | str | None = None) -> dict[str, str]:
    pyproject = MaxsonPyProject(path)

    import_name = pyproject.import_name or ""
    app_name = pyproject.app_name or ""
    app_name_kebab = to_kebab_case(app_name)
    pretty_name = pyproject.pretty_name or app_name_kebab
    description = pyproject.description or f"{pretty_name} application."

    return {
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
        "PRETTY_NAME": pretty_name,
        "DESCRIPTION": description,
    }


def run_init_deb(root_dir: Path | str | None = None) -> list[Path]:
    """Scaffold packaging/deb/ assets and return generated file paths."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_deb_metadata(target_dir / "pyproject.toml")

    deb_dir = target_dir / "packaging" / "deb"
    deb_dir.mkdir(parents=True, exist_ok=True)

    app_name = meta["APP_NAME"]

    files_to_create = {
        deb_dir / "control.in": CONTROL_TEMPLATE,
        deb_dir / f"{app_name}.desktop": DESKTOP_TEMPLATE,
        deb_dir / "launcher.sh": LAUNCHER_TEMPLATE,
    }

    created_paths: list[Path] = []
    for path, template in files_to_create.items():
        write_str_to_file(path=path, text=template.format(**meta))
        created_paths.append(path)

    return created_paths
