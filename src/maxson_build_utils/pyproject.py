# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

_MISSING = object()

def get_toml_value(
    pyproject: str | Path,
    *keys: str,
    default: Any = _MISSING,
) -> Any:
    """
    Extract a nested value from a TOML file.

    Example:
        get_toml_value("pyproject.toml", "project", "name")
        -> "my-package"

        get_toml_value("pyproject.toml", "tool", "maxson-build-utils", "pretty-name")
    """
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


def get_project_name(pyproject: str | Path) -> str:
    return get_toml_value(pyproject, "project", "name")


def get_project_version(pyproject: str | Path) -> str:
    return get_toml_value(pyproject, "project", "version")


def get_project_description(pyproject: str | Path) -> str:
    return get_toml_value(pyproject, "project", "description")


def get_project_dependencies(pyproject: str | Path) -> list[str]:
    return get_toml_value(pyproject, "project", "dependencies")


def get_project_urls(pyproject: str | Path) -> dict[str, str]:
    return get_toml_value(pyproject, "project", "urls")
