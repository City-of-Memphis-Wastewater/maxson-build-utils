# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

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

def get_project_name(pyproject: str | Path | None = None) -> str:
    return get_toml_value("project", "name", pyproject=pyproject)


def get_project_version(pyproject: str | Path | None = None) -> str:
    return get_toml_value("project", "version", pyproject=pyproject)


def get_project_description(pyproject: str | Path | None = None) -> str:
    return get_toml_value("project", "description", pyproject=pyproject)


def get_project_dependencies(pyproject: str | Path | None = None) -> list[str]:
    return get_toml_value("project", "dependencies", pyproject=pyproject)


def get_project_urls(pyproject: str | Path | None = None) -> dict[str, str]:
    return get_toml_value("project", "urls", pyproject=pyproject)


# ---

class PyProject:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else Path.cwd() / "pyproject.toml"

        with self.path.open("rb") as f:
            self.data = tomllib.load(f)

    def get(self, *keys: str, default: Any = _MISSING) -> Any:
        value: Any = self.data

        for key in keys:
            try:
                value = value[key]
            except (KeyError, TypeError):
                if default is not _MISSING:
                    return default
                raise

        return value

    @property
    def name(self) -> str:
        return self.get("project", "name")

    @property
    def version(self) -> str:
        return self.get("project", "version")

    @property
    def description(self) -> str:
        return self.get("project", "description")

    @property
    def dependencies(self) -> list[str]:
        return self.get("project", "dependencies", default=[])

    @property
    def urls(self) -> dict[str, str]:
        return self.get("project", "urls", default={})

# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
