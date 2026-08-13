# src/maxson_build_utils/init.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .packaging import (
    flatpak,
    deb, 
    msix, 
    dmg, 
    appimage, 
    PackageType
    )
from .icons import copy_stock_icons
from .pyproject import PyProject
"""
Implement src/*/ dir with __init__.py (possibly a template), when init-src is called
Also init_icons
"""


def run_init_icons(dst:Path|str|None=None):
    # write is dead, dont expect to write to pyproject.toml
    # but we can print to console a recommended cooy and paste pyptoject.toml section
    # what a smell
    keys = ["tool","maxson-build-utils","icons"]
    if dst is None:
        dst = run_init_src() / "data" / "icons"

    return copy_stock_icons(dst)

def run_init_src()->Path:
    """intended to be run after uv init"""
    keys=["tool","maxson-build-utils","names","import"]
    pyproject=PyProject()
    import_name=pyproject.get(*keys)
    if import_name is None:
        import_name=pyproject.name_to_snake_case()
        import_name_dict = pyproject.write(keys=keys,value=import_name)
    src_dir = Path.cwd() /"src"/ import_name
    src_dir.mkdir(parents=True, exist_ok=True)
    return src_dir

def run_init_changelog():
    """Write blank changelog file to docs/CHANGELOG.md"""
    changelog = Path.cwd() / "docs" / "CHANGELOG.md"
    new_changelog="""
# Changelog

All notable changes to this project will be documented in this file.
The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.0] - YYYY-MM-DD
### Added:
-

---
"""

    if not changelog.exists():
        changelog.parent.mkdir(parents=True, exist_ok=True)
        with changelog.open("w", encoding="utf-8") as f:
            f.write(new_changelog)
    else:
        logger.debug(f"CHANGELOG.md already exists at {changelog}")
    return changelog

def run_init_packaging(PackageType)->dict:
    """generate contents of packaging/flatpak"""
    pass


def run_init_packaging_all():
    pass

def run_init_all() -> dict:
    return {
        "src": run_init_src(),
        "changelog": run_init_changelog(),
        "icons": run_init_icons(),
        "packaging": run_init_packaging_all(),
    }


