# src/maxson_build_utils/scaffold/flatpak.py
from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file, WriteResult
from ...names import to_kebab_case
from ...pyproject import MaxsonPyProject

MANIFEST_TEMPLATE = """id: {APP_ID}
runtime: org.freedesktop.Platform
runtime-version: '24.08'
sdk: org.freedesktop.Sdk
command: {APP_NAME}

build-options:
  env:
    APP_ID: {APP_ID}
    APP_NAME: {APP_NAME}
    IMPORT_NAME: {IMPORT_NAME}

modules:
  - name: {APP_NAME}
    buildsystem: simple
    build-commands:
      # 1. Install wheel
      - pip3 install --ignore-installed --no-index --find-links=vendor-wheels --prefix=/app dist/*.whl

      # 2. Desktop Integration Files
      - install -Dm644 packaging/flatpak/$APP_ID.desktop /app/share/applications/$APP_ID.desktop
      - install -Dm644 packaging/flatpak/$APP_ID.metainfo.xml /app/share/metainfo/$APP_ID.metainfo.xml
      - install -Dm644 src/$IMPORT_NAME/data/icons/placeholder.svg /app/share/icons/hicolor/scalable/apps/$APP_ID.svg

      # 3. License
      - install -Dm644 LICENSE /app/share/licenses/$APP_NAME/LICENSE
    sources:
      - type: dir
        path: .
"""

DESKTOP_TEMPLATE = """[Desktop Entry]
Name={APP_NAME}
Exec={APP_NAME}
Icon={APP_ID}
Type=Application
Categories=Utility;
"""

METAINFO_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>{APP_ID}</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>MIT</project_license>
  <name>{APP_NAME}</name>
  <summary>Application generated with maxson-build-utils</summary>
  <launchable type="desktop-id">{APP_ID}.desktop</launchable>
</component>
"""


def resolve_flatpak_metadata(path: Path | str | None = None) -> dict[str, str]:
    pyproject = MaxsonPyProject(path)

    import_name = pyproject.import_name
    app_name = pyproject.app_name
    app_name_kebab = to_kebab_case(app_name)

    app_id = pyproject.get("tool", "maxson-build-utils", "flatpak", "app-id")
    if not app_id:
        app_id = pyproject.get("tool", "maxson-build-utils", "packaging", "flatpak", "app-id")

    if not app_id:
        domain = pyproject.get("tool", "maxson-build-utils", "flatpak", "domain") or "io.github"
        org = pyproject.get("tool", "maxson-build-utils", "flatpak", "org") or "city_of_memphis_wastewater"
        org_clean = org.replace("-", "_").replace(" ", "_").lower()
        app_id = f"{domain}.{org_clean}.{app_name_kebab}"

    return {
        "APP_ID": app_id,
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
    }


def run_init_flatpak_defunct(root_dir: Path | str | None = None) -> list[Path]:
    """Scaffold packaging/flatpak/ assets and return generated file paths."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_flatpak_metadata(target_dir / "pyproject.toml")

    flatpak_dir = target_dir / "packaging" / "flatpak"
    flatpak_dir.mkdir(parents=True, exist_ok=True)

    app_id = meta["APP_ID"]

    files_to_create = {
        flatpak_dir / f"{app_id}.yaml": MANIFEST_TEMPLATE,
        flatpak_dir / f"{app_id}.desktop": DESKTOP_TEMPLATE,
        flatpak_dir / f"{app_id}.metainfo.xml": METAINFO_TEMPLATE,
    }

    created_paths: list[Path] = []
    for path, template in files_to_create.items():
        write_str_to_file(path=path, text=template.format(**meta))
        created_paths.append(path)

    return created_paths


def run_init_flatpak(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    """Scaffold packaging/flatpak/ assets."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_flatpak_metadata(target_dir / "pyproject.toml")

    flatpak_dir = target_dir / "packaging" / "flatpak"
    flatpak_dir.mkdir(parents=True, exist_ok=True)

    app_id = meta["APP_ID"]

    files_to_create = {
        flatpak_dir / f"{app_id}.yaml": MANIFEST_TEMPLATE,
        flatpak_dir / f"{app_id}.desktop": DESKTOP_TEMPLATE,
        flatpak_dir / f"{app_id}.metainfo.xml": METAINFO_TEMPLATE,
    }

    results: list[WriteResult] = []

    for path, template in files_to_create.items():
        results.append(
            write_str_to_file(
                path=path,
                text=template.format(**meta),
            )
        )

    return results
