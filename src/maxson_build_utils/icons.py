# src/maxson_build_utils/icons.py
from pathlib import Path
from importlib.resources import files

def bundled_icons():
    return files("maxson_build_utils") / "data" / "icons"

def copy_stock_icons(path:Path|str|None=None):
    """path arg is a dir, not a file path"""
    if path is None:
        path = Path("src") / "*" / "data" / "icons"
    i=bundled_icons()
    shutil.copy2(i,path)
