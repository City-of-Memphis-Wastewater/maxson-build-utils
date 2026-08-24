# src/maxson_build_utils/helpers.py
from __future__ import annotations
from enum import Enum
from pathlib import Path
import sys
import pyhabitat
import logging
from rich.console import Console

console_stdout = Console()

logger = logging.getLogger(__name__)

class PyinsMode(str, Enum):
    ONEDIR = "onedir"
    ONEFILE = "onefile"

class IconFileType(str, Enum):
    PNG = "png"
    ICO = "ico"
    SVG = "svg"

@dataclass(frozen=True)
class WriteResult:
    path: Path
    created: bool
    overwritten: bool
    def __bool__(self) -> bool:
        return self.created or self.overwritten

def write_str_to_file(
    path: str | Path | None,
    text: str,
    overwrite: bool = False,
) -> WriteResult:
    """Write text to a file and report what happened."""
    if path is None:
        raise ValueError(
            "Cannot write to a file path of 'None'. "
            "Ensure a valid path or root_dir is supplied."
        )

    resolved_path = Path(path).expanduser().resolve()

    existed = resolved_path.exists()

    if existed and not overwrite:
        return WriteResult(
            path=resolved_path,
            created=False,
            overwritten=False,
        )

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with resolved_path.open("w", encoding="utf-8") as f:
        f.write(text)

    return WriteResult(
        path=resolved_path,
        created=not existed,
        overwritten=existed,
    )

def print_write_result(result: WriteResult) -> None:
    if result.created:
        console_stdout.print(f"Created {result.path}")
    elif result.overwritten:
        console_stdout.print(f"Overwrote {result.path}")
    else:
        console_stdout.print(f"Already exists: {result.path}")

def form_dynamic_name(pkg_name: str, version: str, mode: PyinsMode|None = None) -> str:
    """Creates a standardized binary name descriptor."""

    system = pyhabitat.SystemInfo()
    os_tag = system.get_os_tag()
    arch = system.get_arch()
    py_ver = f"py{sys.version_info.major}{sys.version_info.minor}"
    executable_descriptor = f"{pkg_name}-{version}-{py_ver}-{os_tag}-{arch}"
    if mode == PyinsMode.ONEFILE:
        executable_descriptor += f"-{PyinsMode.ONEFILE.value}"
    return executable_descriptor

def resolve_icon_filetype(icon_src: Path) -> IconFileType | None:
    """Resolves and validates the extension of a given icon path."""
    suffix = icon_src.suffix.lower().removeprefix(".")
    try:
        return IconFileType(suffix)
    except ValueError:
        return None

#def get_cli_main_file(project_root: Path, src_folder_name: str) -> Path:
#    """Locates the entry point module inside the package source folder."""
#    return project_root / "src" / src_folder_name / "__main__.py"


def resolve_icon_path(provided_icon: Path | str | None) -> Path:
    """Resolves icon path from explicit argument, glob search, or asset fallback."""
    # 1. Explicit input provided and exists
    if provided_icon and str(provided_icon).strip():
        icon_path = Path(provided_icon).expanduser().resolve()
        if icon_path.exists():
            return icon_path
        logger.warning("Specified icon '%s' not found. Attempting auto-discovery...", provided_icon)

    # 2. Glob pattern discovery: src/*/data/icons/*.png
    matches = sorted(Path("src").glob("*/data/icons/*.png"))
    if matches:
        found_icon = matches[0].resolve()
        logger.info("Auto-discovered icon: %s", found_icon)
        return found_icon

    # 3. Fallback to assets/icon.png if present
    fallback_assets = Path("assets/icon.png").resolve()
    if fallback_assets.exists():
        return fallback_assets

    raise FileNotFoundError(
        "Could not resolve an icon path. Searched explicit input, "
        "'src/*/data/icons/*.png', and 'assets/icon.png'."
    )
