# src/maxson_build_utils/builders/validate.py
from enum import Enum
from pyhabitat import AppMode, probe_app_mode_mgu

class TargetBuild(str, Enum):
    DMG = "dmg"
    MSIX = "msix"
    FLATPAK = "flatpak"
    APPIMAGE = "appimage"
    DEB = "deb"

DESKTOP_ONLY_TARGETS = {
    TargetBuild.DMG,
    TargetBuild.MSIX,
    TargetBuild.FLATPAK,
}

def validate_build_target(target_format: TargetBuild) -> None:
    app_mode = probe_app_mode_mgu()
    if target_format in DESKTOP_ONLY_TARGETS and app_mode != AppMode.GUI:
        raise ValueError(
            f"Target format '{target_format.value}' requires GUI support. "
            f"Ensure GUI dependencies ('maxson-gui-utils') are present."
        )

