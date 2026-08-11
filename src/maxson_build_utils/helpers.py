# maxson_build_utils/src/maxson_build_utils/helpers.py
from __future__ import annotations
from enum import Enum
from pathlib import Path
import sys
import pyhabitat


class PyinsMode(str, Enum):
    ONEDIR = "onedir"
    ONEFILE = "onefile"

class IconFileType(str, Enum):
    PNG = "png"
    ICO = "ico"
    SVG = "svg"


def form_dynamic_name(pkg_name: str, version: str, mode: PyinsMode|None = None) -> str:
    """Creates a standardized binary name descriptor."""

    os_tag = pyhabitat.SystemInfo().get_os_tag()
    arch = pyhabitat.SystemInfo().get_arch()
    py_ver = f"py{sys.version_info.major}{sys.version_info.minor}"
    dynamic_exe_name = f"{pkg_name}-{version}-{py_ver}-{os_tag}-{arch}"
    if mode == PyinsMode.ONEFILE:
        dynamic_exe_name += f"-{PyinsMode.ONEFILE.value}"
    return dynamic_exe_name

def resolve_icon_filetype(icon_src: Path) -> IconFileType | None:
    """Resolves and validates the extension of a given icon path."""
    suffix = icon_src.suffix.lower().removeprefix(".")
    try:
        return IconFileType(suffix)
    except ValueError:
        return None

def get_cli_main_file(project_root: Path, src_folder_name: str) -> Path:
    """Locates the entry point module inside the package source folder."""
    return project_root / "src" / src_folder_name / "__main__.py"




