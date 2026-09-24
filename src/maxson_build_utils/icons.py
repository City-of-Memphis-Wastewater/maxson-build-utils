# src/maxson_build_utils/icons.py
import shutil
from pathlib import Path
from importlib.resources import files

from .pyproject import MaxsonPyProject
from .helpers import WriteResult  

def bundled_icons():
    return files("maxson_build_utils") / "data" / "icons"

def copy_stock_icons_defunct(
    dst: Path | str | None = None,
    root_dir: Path | str | None = None
    ) -> Path:
    if dst is None:
        pyproject = MaxsonPyProject(root_dir) # force local pyproject.toml
        dst = pyproject.icons_dir

    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for icon in bundled_icons().iterdir():
        if icon.is_file():
            shutil.copy2(icon, dst / icon.name)

    return dst

def copy_stock_icons(
    dst: Path | str | None = None,
    root_dir: Path | str | None = None,
    overwrite: bool = False, # Added overwrite toggle defaulting to False
) -> list[WriteResult]: # Updated type hint to match the returned results list
    if dst is None:
        pyproject = MaxsonPyProject(root_dir) # force local pyproject.toml
        dst = pyproject.icons_dir

    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    results: list[WriteResult] = []

    for icon in bundled_icons().iterdir():
        if icon.is_file():
            target_path = dst / icon.name
            existed = target_path.exists()

            # Early exit for the specific file if overwrite is disabled
            if existed and not overwrite:
                results.append(
                    WriteResult(path=target_path, created=False, overwritten=False)
                )
                continue

            shutil.copy2(icon, target_path)
            results.append(
                WriteResult(path=target_path, created=not existed, overwritten=existed)
            )

    return results
