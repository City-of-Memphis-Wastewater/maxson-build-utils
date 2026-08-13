# src/maxson-build-utils/packaging.py
from __future__ import annotations
import logging

from enum import Enum
logger = logging.getLogger(__name__)
"""
inferred cli sub app
mbu init-packaging deb
mbu init-packaging appimage
mbu init-packaging flatpak
mbu init-packaging msix
mbu init-packaging dmg
"""

def PackageType(str, Enum):
    flatpak:FLATPAK
    deb:DEB
    msix:MSIX
    dmg:DMG
    appimage:APPIMAGE

def flatpak():
    pass

def msix():
    pass

def appimage():
    pass

def dmg():
    pass

def deb():
    pass
