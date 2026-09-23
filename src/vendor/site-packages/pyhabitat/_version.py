# src/pyhabitat/_version.py
from pathlib import Path

def get_version() -> str:
    # 1. Try local VERSION file FIRST (Source/Dev/Bundled)
    # This ensures that even if an old version is installed via pip,
    # the code currently running uses its own sibling VERSION file.
    try:
        # Path relative to this file: src/pyhabitat/VERSION
        version_file = Path(__file__).resolve().parent / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        print("VERSION not found")
        pass

    # 2. Fallback to metadata (Installed via pip without source available)
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("pyhabitat")
    except (ImportError, PackageNotFoundError):
        pass

    return "0.0.0-unknown"

__version__ = get_version()
