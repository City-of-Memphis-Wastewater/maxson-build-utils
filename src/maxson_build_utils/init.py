# src/maxson_build_utils/init
from .packaging import flatpak, deb, msix, dmg, appimage
"""
Implement src/*/ dir with __init__.py (possibly a template), when init-src is called
Also init_icons
"""

def init_icons():
    pass

def init_src():
    """intended to be run after uv init"""
    pass

def init_changelog():
    pass

def init_flatpak():
    """generate contents of packaging/flatpak"""
    pass

    
