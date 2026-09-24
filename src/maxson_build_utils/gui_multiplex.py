# src/maxson_build_utils/gui_multiplex.py
from __future__ import annotations
from enum import Enum
from pathlib import Path
import sys
import pyhabitat
from rich.console import Console
import logging

logger = logging.getLogger(__name__)

class GuiInterface(str, Enum):
    NONE = "none"
    TKINTER = "tkinter"
    KIVY = "kivy"
    WEBVIEW = "webview"
