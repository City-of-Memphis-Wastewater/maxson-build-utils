#!/usr/bin/env python3 
# build_utils/build_utils.py

from __future__ import annotations
import pyhabitat
from enum import Enum
import sys
import logging

class PyinsMode(str, Enum):
    """onedir vs onefile"""
    ONEDIR = "onedir"
    ONEFILE = "onefile"

# --- Dynamic Naming Placeholder (Simplified version for this context) ---
def form_dynamic_name(pkg_name: str, version: str, mode: PyinsMode|None = None) -> str:
    """Creates a standardized binary name descriptor."""

    os_tag = pyhabitat.SystemInfo().get_os_tag()
    arch = pyhabitat.SystemInfo().get_arch()
    py_ver = f"py{sys.version_info.major}{sys.version_info.minor}"
    dynamic_exe_name = f"{pkg_name}-{version}-{py_ver}-{os_tag}-{arch}"
    if mode == PyinsMode.ONEFILE:
        dynamic_exe_name += f"-{PyinsMode.ONEFILE.value}"
    return dynamic_exe_name
