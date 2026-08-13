# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any,List
import json

from .names import to_snake_case

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

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

    def name_to_snake_case(self):
        return to_snake_case(self.get("project","name"))

    def write(self, keys: list[str], value: Any) -> None:
        pass

# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
