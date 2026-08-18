# src/version/pyproject.py
from __future__ import annotations
from pathlib import Path

from .pyproject import PyProject


def get_version(path: str | Path | None = None) -> str:
    project = PyProject(path)

    version = project.get("project", "version")

    if version is not None:
        return version

    dynamic = project.get("project", "dynamic")

    if "version" not in dynamic:
        raise ValueError("No project version found")

    # setuptools-specific dynamic version resolution
    version_config = project.get(
        "tool",
        "setuptools",
        "dynamic",
        "version",
    )

    version_file = version_config.get("file")

    if version_file:
        version_path = project.path.parent / version_file
        return version_path.read_text().strip()

    raise ValueError("Unable to resolve dynamic project version")
