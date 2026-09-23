# src/dworshak_secret/_version.py
from pathlib import Path

PACKAGE_NAME = "dworshak-secret"

def get_version() -> str:
    # Try local VERSION file (Source/Dev)
    try:
        version_file = Path(__file__).parent / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
    except Exception:
        pass

    # Try metadata (Installed)
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version(PACKAGE_NAME)
    except (ImportError, PackageNotFoundError):
        pass
    return "0.0.0-unknown"
__version__ = get_version()
