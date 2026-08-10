# maxson_build_utils/src/maxson_build_utils/helpers.py
from __future__ import annotations
from enum import Enum

from typing import Any


def form_dynamic_name(src_folder_name: str, version: str, mode: Any = None) -> str:
    """Forms a dynamic output artifact base name."""
    if mode is None:
        return f"{src_folder_name}-{version}"

    mode_str = mode.value if hasattr(mode, "value") else str(mode)
    return f"{src_folder_name}-{version}-{mode_str}"

class PyinsMode(str, Enum):
    ONEDIR = "onedir"
    ONEFILE = "onefile"

class IconFileType(str, Enum):
    PNG = "png"
    ICO = "ico"
    SVG = "svg"
