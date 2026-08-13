# src/maxson_build_utils/names.py
from __future__ import annotations
import re
from pathlib import Path

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

def get_import_name(path:str|Path|None=None) -> str:
    from .pyproject import PyProject
    keys=["tool","maxson-build-utils","names","import"]
    pyproject=PyProject(path)
    import_name=pyproject.get(*keys)
    if import_name is None:
        import_name=pyproject.name_to_snake_case()
    return import_name
# Alias for backward compatibility
get_src_name = get_import_name

def get_src_dir(path:str|Path|None=None) -> Path:
    import_name = get_src_name(path)
    src_dir = Path.cwd() /"src"/ import_name
    return src_dir

def get_pretty_name(path:str|Path|None=None) -> str:
    from .pyproject import PyProject
    keys=["tool","maxson-build-utils","names","pretty"]
    pyproject=PyProject(path)
    pretty_name=pyproject.get(*keys)
    if pretty_name is None:
        pretty_name=pyproject.name_to_title_case()
    return pretty_name

def get_app_name(path:str|Path|None=None) -> str:
    from .pyproject import PyProject
    keys=["project","name"]
    pyproject=PyProject(path)
    app_name=pyproject.get(*keys)
    if app_name is None:
        app_name=pyproject.name_to_title_case()
    return app_name


