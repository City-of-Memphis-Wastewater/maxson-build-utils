# src/maxson_build_utils/scaffold/flatpak.py
from __future__ import annotations

from pathlib import Path

from ..helpers import write_str_to_file
from ..names import to_kebab_case
from ..pyproject import PyProject


def resolve_flatpak_metadata(path: Path | str | None = None) -> dict[str, str]:
    pyproject = PyProject(path)

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

# MANIFEST_TEMPLATE, DESKTOP_TEMPLATE, METAINFO_TEMPLATE stay here...

def run_init_flatpak(root_dir: Path | str | None = None) -> list[Path]:
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
