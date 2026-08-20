# src/maxson_build_utils/scaffold/version.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject

def run_init_version(root_dir: Path | str | None = None) -> None:
    pyproject = MaxsonPyProject(root_dir)

    raw_version_str='''
# src/__IMPORT_NAME__/_version.py
from pathlib import Path
from .context import APP_NAME
def get_version() -> str:
    try:
        version_file = Path(__file__).parent / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        pass

    # Try metadata (Installed)
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version(APP_NAME)
    except (ImportError, PackageNotFoundError):
        pass


    return "0.0.0-unknown"

__version__ = get_version()
'''
    raw_version_str=raw_version_str.replace("__IMPORT_NAME__", pyproject.import_name)
    write_str_to_file(pyproject.src_dir / "_version.py", text = raw_version_str)

def run_init_version_num(root_dir: Path | str | None = None) -> None:
    pyproject = MaxsonPyProject(root_dir)

    raw_version_num_str='''
0.1.0

'''
    raw_version_num_str=raw_version_num_str.replace("__IMPORT_NAME__", pyproject.import_name)
    write_str_to_file(pyproject.src_dir / "VERSION", text = raw_version_num_str)
