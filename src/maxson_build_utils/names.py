# src/maxson_build_utils/names.py
from __future__ import annotations
import re

def to_snake_case(value: str) -> str:
    """Convert a string to snake_case."""
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    return value.strip("_").lower()


def to_kebab_case(value: str) -> str:
    """Convert a string to kebab-case."""
    return to_snake_case(value).replace("_", "-")


def to_title_case(value: str) -> str:
    """Convert a string to Title Case."""
    words = re.split(r"[-_\s]+", value.strip())
    return " ".join(word.capitalize() for word in words if word)

def to_pascal_case(value: str) -> str:
    """Convert a kebab, snake, or space-delimited string to PascalCase without spaces."""
    words = re.split(r"[-_\s]+", value.strip())
    return "".join(word.capitalize() for word in words if word)