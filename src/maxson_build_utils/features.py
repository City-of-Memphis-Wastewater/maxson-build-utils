# src/maxson_build_utils/features.py
from __future__ import annotations

import importlib.util
from enum import Enum, auto
import pyhabitat

class AppMode(Enum):
    GUI = auto()
    CLI = auto()


def probe_app_mode(gui_extension_package: str = "maxson_gui_utils") -> AppMode:
    """
    Determines if an application should run in GUI or CLI mode.
    
    Returns AppMode.GUI only if Tkinter/Display is available AND 
    the requested GUI helper package is importable.
    """
    if not pyhabitat.tkinter_is_available():
        return AppMode.CLI

    if importlib.util.find_spec(gui_extension_package) is None:
        return AppMode.CLI

    return AppMode.GUI
