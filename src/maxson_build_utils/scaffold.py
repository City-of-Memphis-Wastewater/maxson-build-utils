# src/maxson_build_utils/init.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .helpers import write_str_to_file
from .packaging import (
    flatpak,
    deb, 
    msix, 
    dmg, 
    appimage, 
    PackageType
    )
from .icons import copy_stock_icons, bundled_icons
from .pyproject import PyProject

"""
Implement src/*/ dir with __init__.py (possibly a template), when init-src is called
Also init_icons
"""


def run_init_icons(
    dst:Path|str|None=None,
    root_dir: Path | str | None = None
    ) -> Path:
    # write is dead, dont expect to write to pyproject.toml
    # but we can print to console a recommended cooy and paste pyptoject.toml section
    # what a smell
    #keys = ["tool","maxson-build-utils","icons"]
    if dst is None:
        pyproject = PyProject(root_dir)
        dst = pyproject.icons_dir

    dst = Path(dst)

    if dst.resolve() == Path(bundled_icons()).resolve():
        logger.debug("Stock icon destination is the bundled icon directory; nothing to copy.")
        return dst

    return copy_stock_icons(dst)


def run_init_src()->Path:
    """intended to be run after uv init"""
    src_dir = get_src_dir()
    src_dir.mkdir(parents=True, exist_ok=True)
    return src_dir

def run_init_changelog()->Path:
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
    write_str_to_file(path=changelog,text=new_changelog)
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


