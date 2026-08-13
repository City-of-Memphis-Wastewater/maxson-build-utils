# src/maxson_build_utils/scaffold_flatpak.py
from __future__ import annotations

from pathlib import Path
from .helpers import write_str_to_file
from .names import to_kebab_case
from .pyproject import PyProject

def resolve_flatpak_metadata(path: Path | str | None = None) -> dict[str, str]:
    """Resolve APP_ID, APP_NAME, and IMPORT_NAME using pyproject.toml configuration

    or intelligent defaults.
    """
    pyproject = PyProject(path)

    # 1. Resolve IMPORT_NAME (e.g. 'cellshift' or 'maxson_build_utils')
    import_name = pyproject.import_name # expected to be snake case, but src/*/ pathing is what matters

    # 2. Resolve APP_NAME (e.g. 'cellshift' or 'maxson-build-utils')
    app_name = pyproject.app_name
    app_name_kebab = to_kebab_case(app_name) # expected to already be kebab, but ensures it

    # 3. Resolve APP_ID
    # Check explicit app-id first
    app_id = pyproject.get("tool", "maxson-build-utils", "flatpak", "app-id")
    if not app_id:
        app_id = pyproject.get("tool", "maxson-build-utils", "packaging", "flatpak", "app-id")

    if not app_id:
        # Fallback to composable domain + org + app_name
        domain = pyproject.get("tool", "maxson-build-utils", "flatpak", "domain") or "io.github"
        org = pyproject.get("tool", "maxson-build-utils", "flatpak", "org") or "city_of_memphis_wastewater"
        
        # Standardize org name (replace hyphens/spaces with underscores for reverse-DNS compliance)
        org_clean = org.replace("-", "_").replace(" ", "_").lower()
        app_id = f"{domain}.{org_clean}.{app_name_kebab}"

    return {
        "APP_ID": app_id,
        "APP_NAME": app_name_kebab,
        "IMPORT_NAME": import_name,
    }


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


def run_init_flatpak(root_dir: Path | str | None = None) -> None:
    """Scaffold the packaging/flatpak/ directory with standard assets."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    meta = resolve_flatpak_metadata(target_dir / "pyproject.toml")

    flatpak_dir = target_dir / "packaging" / "flatpak"
    flatpak_dir.mkdir(parents=True, exist_ok=True)

    app_id = meta["APP_ID"]

    # Write files using APP_ID in the filename stem
    write_str_to_file(
        path=flatpak_dir / f"{app_id}.yaml",
        text=MANIFEST_TEMPLATE.format(**meta),
    )
    write_str_to_file(
        path=flatpak_dir / f"{app_id}.desktop",
        text=DESKTOP_TEMPLATE.format(**meta),
    )
    write_str_to_file(
        path=flatpak_dir / f"{app_id}.metainfo.xml",
        text=METAINFO_TEMPLATE.format(**meta),
    )
