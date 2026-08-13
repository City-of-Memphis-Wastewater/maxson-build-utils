# src/maxson_build_utils/icons.py
import shutil
from pathlib import Path
from importlib.resources import files

from .names import get_src_dir

def bundled_icons():
    return files("maxson_build_utils") / "data" / "icons"

def copy_stock_icons(path: Path | str | None = None):
    """Copy bundled stock icons into a destination directory."""
    if path is None:
        path = get_src_dir() / "data" / "icons"

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    for icon in bundled_icons().iterdir():
        if icon.is_file():
            shutil.copy2(icon, path / icon.name)
