# src/maxson_build_utils/_version.py
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
