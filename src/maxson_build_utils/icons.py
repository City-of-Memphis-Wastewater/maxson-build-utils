# src/maxson_build_utils/icons.py
import shutil
from pathlib import Path
from importlib.resources import files

from .pyproject import PyProject

def bundled_icons():
    return files("maxson_build_utils") / "data" / "icons"

def copy_stock_icons(
    dst: Path | str | None = None,
    root_dir: Path | str | None = None
    ) -> Path:
    if dst is None:
        pyproject = PyProject(root_dir) # force local pyproject.toml
        dst = pyproject.icons_dir

    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for icon in bundled_icons().iterdir():
        if icon.is_file():
            shutil.copy2(icon, dst / icon.name)

    return dst
