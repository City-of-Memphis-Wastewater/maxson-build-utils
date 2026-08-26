# src/maxson_build_utils/entry.py

from __future__ import annotations


def get_cli_entry_point(import_name: str) -> str:
    """Return the canonical CLI entry point for a Maxson project."""
    return f"{import_name}.__main__:app"
