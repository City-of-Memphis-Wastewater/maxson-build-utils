# src/maxson_build_utils/scaffold/__init__.py
from __future__ import annotations

# --- packaging ---
from .icons import run_init_icons
from .appimage import run_init_appimage
from .deb import run_init_deb
from .dmg import run_init_dmg
from .flatpak import run_init_flatpak
from .msix import run_init_msix
from .pyinstaller import run_init_pyinstaller
from .shiv import run_init_shiv

__all__ = [
    # --- packaging ---
    "run_init_icons",
    "run_init_appimage",
    "run_init_deb",
    "run_init_dmg",
    "run_init_flatpak",
    "run_init_msix",
    "run_init_pyinstaller",
    "run_init_shiv",

]
