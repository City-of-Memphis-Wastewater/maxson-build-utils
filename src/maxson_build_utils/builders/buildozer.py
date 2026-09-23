# src/maxson_build_utils/builders/buildozer.py
from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import subprocess

from ..vendor import VENDOR_SITE_PACKAGES_DIR

class BuildozerMode(StrEnum):
    APK = "apk"
    AAB = "aab"

    @property
    def buildozer_command(self) -> tuple[str, ...]:
        return {
            BuildozerMode.APK: ("android", "debug"),
            BuildozerMode.AAB: ("android", "release"),
        }[self]


def build_buildozer(
    mode: BuildozerMode = BuildozerMode.APK,
    *,
    root_dir: Path | str | None = None,
    check_vendor: bool = True,
    vendor_dir: Path | None = None,
) -> Path:
    """Build an Android application using Buildozer."""

    root = Path(root_dir) if root_dir else Path.cwd()
    spec_dir = root / "packaging" / "buildozer"
    spec_path = spec_dir / "buildozer.spec"

    if not spec_path.exists():
        raise FileNotFoundError(
            f"Buildozer spec not found: {spec_path}\n"
            "Run `mbu init packaging buildozer` first."
        )

    if not (spec_dir / "buildozer.spec").is_file():
        raise FileNotFoundError(spec_path)

    # 1. Pre-flight vendor validation
    if check_vendor:
        target_vendor = vendor_dir or VENDOR_SITE_PACKAGES_DIR
        validate_vendor_site_packages(target_vendor)

    command = (
        "uv",
        "run",
        "buildozer",
        *mode.buildozer_command,
    )

    subprocess.run(
        command,
        cwd=spec_dir,
        check=True,
    )

    return spec_dir

def validate_vendor_site_packages(vendor_dir: Path) -> None:
    """Verifies that the vendored site-packages directory exists and is not empty."""
    if not vendor_dir.exists() or not any(vendor_dir.iterdir()):
        raise RuntimeError(
            f"Vendored packages directory is missing or empty at:\n  {vendor_dir}\n\n"
            "Pre-flight check failed! Please populate vendored site-packages before building:\n"
            "  uv run mbu vendor site-packages"
        )
