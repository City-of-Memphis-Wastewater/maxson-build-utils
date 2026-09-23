# src/maxson_build_utils/builders/buildozer.py
from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import subprocess


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
