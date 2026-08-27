# src/maxson_build_utils/scaffold/packaging/deb.py
from __future__ import annotations

from pathlib import Path

from ...helpers import WriteResult, write_str_to_file
from ...names import to_kebab_case
from ...pyproject import MaxsonPyProject

DEFAULT_CONTROL_TEMPLATE = """Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCHITECTURE}
Maintainer: {MAINTAINER}
Description: {DESCRIPTION}
"""

DEFAULT_DESKTOP_TEMPLATE = """[Desktop Entry]
Name={PRETTY_NAME}
Exec={APP_NAME}
Icon={APP_NAME}
Type=Application
Categories=Utility;
Terminal={TERMINAL}
"""

DEFAULT_LAUNCHER_TEMPLATE = """#!/bin/bash
exec /opt/{APP_NAME}/venv/bin/{APP_NAME} "$@"
"""


def resolve_deb_metadata(
    path: Path | str | None = None,
    arch: str = "amd64",
    terminal: bool = False,
) -> dict[str, str]:
    """Extract metadata from pyproject.toml for Debian packaging."""
    pyproject = MaxsonPyProject(path)

    import_name = pyproject.import_name or ""
    app_name = pyproject.app_name or ""
    app_name_kebab = to_kebab_case(app_name)
    pretty_name = pyproject.pretty_name or app_name_kebab
    description = pyproject.description or f"{pretty_name} application."
    maintainer = pyproject.author or "Developer <none@none.com>"
    version = pyproject.version or "0.1.0"

    return {
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
        "PRETTY_NAME": pretty_name,
        "DESCRIPTION": description,
        "MAINTAINER": maintainer,
        "VERSION": version,
        "ARCHITECTURE": arch,
        "TERMINAL": "true" if terminal else "false",
    }


def run_init_deb(
    root_dir: Path | str | None = None,
    overwrite: bool = False,
) -> list[WriteResult]:
    """Scaffold packaging/deb/ assets and return status results."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_deb_metadata(target_dir / "pyproject.toml")

    deb_dir = target_dir / "packaging" / "deb"
    deb_dir.mkdir(parents=True, exist_ok=True)

    app_name = meta["APP_NAME"]

    files_to_create: dict[Path, str] = {
        deb_dir / "control": DEFAULT_CONTROL_TEMPLATE.format(**meta),
        deb_dir / f"{app_name}.desktop": DEFAULT_DESKTOP_TEMPLATE.format(**meta),
        deb_dir / "launcher.sh": DEFAULT_LAUNCHER_TEMPLATE.format(APP_NAME=app_name),
    }

    results: list[WriteResult] = []
    for path, content in files_to_create.items():
        res = write_str_to_file(path=path, text=content, overwrite=overwrite)
        results.append(res)

    return results