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

def to_pascal_case(val: str) -> str:
    # Insert space before capital letters to preserve camel/pascal words
    val = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", val)
    # Replace non-alphanumeric separators with spaces
    words = re.sub(r"[^a-zA-Z0-9]", " ", val).split()
    return "".join(word.capitalize() for word in words if word)


def get_default_identity_name(publisher_display_name: str, pretty_name: str) -> str:
    """msix packaging for windows store"""
    clean_pub = to_pascal_case(publisher_display_name)
    clean_app = to_pascal_case(pretty_name)
    return f"{clean_pub}.{clean_app}"