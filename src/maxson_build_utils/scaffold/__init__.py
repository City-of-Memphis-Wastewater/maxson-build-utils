# src/maxson_build_utils/scaffold/__init__.py
from __future__ import annotations

from .changelog import run_init_changelog
from .cli import run_init_cli
from .context import run_init_context
from .flatpak import run_init_flatpak
from .gui import run_init_gui
from .icons import run_init_icons
from .src import run_init_src
from .pyproject import run_init_pyproject
from .init import run_init_init

__all__ = [
    "run_init_changelog",
    "run_init_cli",
    "run_init_context",
    "run_init_flatpak",
    "run_init_gui",
    "run_init_icons",
    "run_init_src",
    "run_init_pyproject",
    "run_init_init",
]
