# src/maxson_build_utils/builders/dmg.py
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def build_dmg(
    app_path: Path,
    app_name_pretty: str,
    version: str,
    output_dir: Path = Path("dist/dmg/"),
    packaging_dir: Path = Path("packaging/dmg"),
    plist_template: Path | None = None,
) -> Path:
    """Wraps an existing .app bundle into a DMG installer image via create-dmg."""
    if app_path.suffix != ".app":
        raise ValueError(f"Expected a .app bundle, got: {app_path}")

    if shutil.which("create-dmg") is None:
        raise RuntimeError(
            "create-dmg is not installed. Install via: brew install create-dmg"
        )

    settings_path = packaging_dir / "settings.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    dmg_path = output_dir / f"{app_path.stem}.dmg"

    if dmg_path.exists():
        dmg_path.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        staged_app = tmp_path / app_path.name
        shutil.copytree(app_path, staged_app)

        cmd = [
            "create-dmg",
            "--volname", f"{app_name_pretty} {version}",
            "--window-size", "500", "300",
            "--icon-size", "100",
            "--icon", staged_app.name, "150", "180",
            "--app-drop-link", "450", "180",
            str(dmg_path.resolve()),
            str(tmp_path),
        ]
        
        subprocess.run(cmd, check=True)

    return dmg_path
