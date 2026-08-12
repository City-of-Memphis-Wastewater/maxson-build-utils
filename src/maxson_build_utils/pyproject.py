# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

'''
_MISSING = object()

def get_toml_value(
    *keys: str,
    pyproject: str | Path | None = None,
    default: Any = _MISSING,
) -> Any:
    """
    Extract a nested value from a TOML file.

    Example:
        get_toml_value("pyproject.toml", "project", "name")
        -> "my-package"

        get_toml_value("pyproject.toml", "tool", "maxson-build-utils", "pretty-name")
    """
    if pyproject is None:
        pyproject = Path.cwd() / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    value: Any = data
    for key in keys:
        try:
            value = value[key]
        except (KeyError, TypeError):
            if default is not _MISSING:
                return default
            raise

    return value

'''
class PyProject:
    """
    missing → None
    empty string → ""
    empty list → []
    empty dict → {}
    """
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else Path.cwd() / "pyproject.toml"

        with self.path.open("rb") as f:
            self.data = tomllib.load(f)

    def require(self, *keys: str) -> Any:
        value: Any = self.data

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                raise KeyError(".".join(keys))

            value = value[key]

        return value

    def get(self, *keys: str) -> Any | None:
        value: Any = self.data

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None

            value = value[key]

        return value

# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
