# src/maxson_build_utils/target.py

from __future__ import annotations

from pathlib import Path

from ..helpers import PyinsMode
from ..pyproject import MaxsonPyProject

def get_target_project_root() -> Path:
    return Path.cwd()

def get_dist_dir() -> Path:
    return get_target_project_root() / "dist"

# backwards compatibility, technically wrong semantics (hobgoblin of little minds, etc)
TARGET_PROJECT_ROOT = get_target_project_root()
DIST_DIR = get_dist_dir()


MACOS_APP_DIST_DIR = DIST_DIR / "macOS_app"
DMG_DIST_DIR = DIST_DIR / "dmg"

DIST_DIR_ONEFILE = DIST_DIR / PyinsMode.ONEFILE.value
DIST_DIR_ONEDIR = DIST_DIR / PyinsMode.ONEDIR.value


def get_pyproject() -> MaxsonPyProject | None:
    """Parse the target project's pyproject.toml, if available."""

    proj = MaxsonPyProject(TARGET_PROJECT_ROOT)

    if proj.path is None:
        return None

    return proj


def get_description() -> str | None:
    """Return the target project's description, if available."""

    proj = get_pyproject()

    if proj is None:
        return None

    return proj.get("project", "description")


def get_app_name() -> str:
    """Return the target project's package/application name."""

    proj = get_pyproject()

    if proj is not None:
        name = proj.get("project", "name")

        if name:
            return name

    return TARGET_PROJECT_ROOT.name.replace("_", "-")


def get_pretty_name(app_name: str | None = None) -> str:
    """Return a display name for the target project."""

    if app_name is not None:
        return app_name

    return get_app_name()
