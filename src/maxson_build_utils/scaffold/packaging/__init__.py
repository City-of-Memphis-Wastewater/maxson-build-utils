# src/maxson_build_utils/scaffold/__init__.py
from __future__ import annotations

# --- packaging ---
from .icons import run_init_icons
from .flatpak import run_init_flatpak
from .appimage import run_init_appimage

__all__ = [
    # --- packaging ---
    "run_init_icons",
    "run_init_flatpak",
    "run_init_appimage",

]
