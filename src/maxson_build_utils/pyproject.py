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

    # --- Raw Metadata Properties ---

    @property
    def name(self) -> str | None:
        """Raw [project.name] string from TOML."""
        return self.get("project", "name")

    # --- Resolved Naming Properties ---

    @property
    def app_name(self) -> str:
        """Distribution / binary name strictly formatted in kebab-case (e.g. 'maxson-build-utils')."""
        raw_name = self.name or self.path.parent.name
        return to_kebab_case(raw_name)

    @property
    def import_name(self) -> str:
        """Python module import name in snake_case (e.g. 'maxson_build_utils').

        Checks [tool.maxson-build-utils.names.import] first, falling back to
        snake_case(name).
        """
        custom_import = self.get("tool", "maxson-build-utils", "names", "import")
        if custom_import:
            return to_snake_case(custom_import)
        return to_snake_case(self.name or self.path.parent.name)

    @property
    def pretty_name(self) -> str:
        """Human-readable project title (e.g. 'Maxson Build Utils').

        Checks [tool.maxson-build-utils.names.pretty] first, falling back to
        Title Case.
        """
        custom_pretty = self.get("tool", "maxson-build-utils", "names", "pretty")
        if custom_pretty:
            return custom_pretty
        return to_title_case(self.name or self.path.parent.name)

    @property
    def src_dir(self) -> Path:
        """Path to internal src module directory (e.g. project_root / 'src' / import_name)."""
        return self.path.parent / "src" / self.import_name

    # --- Backward-Compatibility Helpers ---

    def name_to_snake_case(self) -> str:
        return to_snake_case(self.name or self.path.parent.name)

    def name_to_title_case(self) -> str:
        return to_title_case(self.name or self.path.parent.name)

# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
