# src/maxson_build_utils/scaffold/packaging/dmg.py
from __future__ import annotations

import json
from pathlib import Path
from string import Template

from ...helpers import WriteResult, write_str_to_file
from ...names import to_title_case
from ...pyproject import MaxsonPyProject

PLIST_TEMPLATE = Template(
    """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$executable_name</string>
    <key>CFBundleIconFile</key>
    <string>$app_name.icns</string>
    <key>CFBundleIdentifier</key>
    <string>$bundle_identifier</string>
    <key>CFBundleName</key>
    <string>$display_name</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>$version</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
)


def render_info_plist(
    executable_name: str,
    app_name: str,
    bundle_identifier: str,
    display_name: str,
    version: str,
) -> str:
    return PLIST_TEMPLATE.substitute(
        executable_name=executable_name,
        app_name=app_name,
        bundle_identifier=bundle_identifier,
        display_name=display_name,
        version=version,
    )


def render_dmg_settings(volname: str) -> str:
    settings = {
        "volname": volname,
        "window_size": [500, 300],
        "icon_size": 100,
        "app_icon_pos": [150, 180],
        "drop_link_pos": [450, 180],
    }
    return json.dumps(settings, indent=2)


def run_init_dmg(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> list[WriteResult]:
    """Scaffold `packaging/dmg/Info.plist` and `settings.json` targets."""
    pyproject = MaxsonPyProject(root_dir)
    root = Path(root_dir) if root_dir else pyproject.root_dir or Path.cwd()

    dmg_dir = root / "packaging" / "dmg"
    dmg_dir.mkdir(parents=True, exist_ok=True)

    dmg_cfg = (
        pyproject.get("tool", "maxson-build-utils", "packaging", "dmg")
        or pyproject.get("tool", "maxson-build-utils", "dmg")
        or {}
    )

    app_name = pyproject.import_name or "app"
    display_name = pyproject.pretty_name or to_title_case(app_name)
    bundle_identifier = (
        dmg_cfg.get("bundle_identifier")
        or f"com.local.{app_name}"
    )
    executable_name = app_name
    version = pyproject.version

    results: list[WriteResult] = []

    # 1. Unversioned Info.plist Template
    results.append(
        write_str_to_file(
            dmg_dir / "Info.plist_unversioned.in",
            text=render_info_plist(
                executable_name=executable_name,
                app_name=app_name,
                bundle_identifier=bundle_identifier,
                display_name=display_name,
                version="@@VERSION_PLACEHOLDER@@",
            ),
            overwrite=overwrite,
        )
    )

    # 2. Rendered Active Info.plist
    results.append(
        write_str_to_file(
            dmg_dir / "Info.plist",
            text=render_info_plist(
                executable_name=executable_name,
                app_name=app_name,
                bundle_identifier=bundle_identifier,
                display_name=display_name,
                version=version,
            ),
            overwrite=overwrite,
        )
    )

    # 3. Rendered settings.json
    volname = f"{display_name} {version}"
    results.append(
        write_str_to_file(
            dmg_dir / "settings.json",
            text=render_dmg_settings(volname=volname),
            overwrite=overwrite,
        )
    )

    return results