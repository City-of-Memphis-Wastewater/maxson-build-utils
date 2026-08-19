# src/maxson_build_utils/scaffold/__init__.py
from __future__ import annotations

from .changelog import run_init_changelog
from .cli import run_init_cli
from .context import run_init_context
from .config import run_init_config
from .core import run_init_core
from .helpers import run_init_helpers
from .flatpak import run_init_flatpak
from .gui import run_init_gui
from .icons import run_init_icons
from .src import run_init_src
from .pyproject import run_init_pyproject
from ._init import run_init_init
from ._main import run_init_main
from .logging_setup import run_init_logging_setup
from .uv import run_uv_init_custom

__all__ = [
    # --- source code --
    "run_init_pyproject",
    "run_init_readme",
    "run_init_gitignore",
    "run_init_git",
    "run_init_changelog",
    "run_init_src",
    "run_init_cli",
    "run_init_context",
    "run_init_config",
    "run_init_gui",
    "run_init_icons",
    "run_init_init",
    "run_init_main",
    "run_init_logging_setup",
    # --- packaging ---
    "run_init_flatpak",
]
