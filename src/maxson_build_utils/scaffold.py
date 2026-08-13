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
from .pyproject import PyProject


def run_init_src(root_dir:Path|None=None)->Path:
    """intended to be run after uv init"""
    pyproject = PyProject(root_dir)
    src_dir = pyproject.src_dir
    src_dir.mkdir(parents=True, exist_ok=True)
    return src_dir

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


