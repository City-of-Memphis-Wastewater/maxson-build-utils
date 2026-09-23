# src/pyhabitat/webcheck.py
from __future__ import annotations
import os
import webbrowser
import shutil
import logging

from .environment import (
    on_termux, 
    on_linux,
    on_windows,
    on_macos,
    on_wsl,
    is_android_kivy
)

logger = logging.getLogger(__name__)

__all__ = [
    'web_browser_is_available',
]

def web_browser_is_available() -> bool:
    """Check if a web browser can be launched in the current environment."""

    if is_android_kivy():
        try:
            from jnius import autoclass
            # Verify Android's PythonActivity and Intent classes can be resolved
            autoclass("org.kivy.android.PythonActivity")
            autoclass("android.content.Intent")
            return True
        except Exception:
            return False
        
    # Termux on Android
    if on_termux() and shutil.which("termux-open-url"):
        return True

    # WSL / Windows Edge bridge
    if on_wsl() and (shutil.which("microsoft-edge") or shutil.which("wslview")):
        return True

    # Linux Desktop GUI launcher
    if on_linux() and shutil.which("xdg-open"):
        return True

    # macOS launcher
    if on_macos() and shutil.which("open"):
        return True

    # Windows native launcher
    if on_windows() and shutil.which("cmd"):
        return True

    # Fallback to standard Python webbrowser registry
    try:
        browser = webbrowser.get()
        return browser is not None
    except (webbrowser.Error, Exception):
        return False
