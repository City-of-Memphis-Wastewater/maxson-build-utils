# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any,List
import json

from .names import to_snake_case, to_kebab_case, to_title_case

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
        if path is None:
            resolved_path = Path.cwd() / "pyproject.toml"
        else:
            p = Path(path)
            resolved_path = p / "pyproject.toml" if p.is_dir() else p

        self.path = resolved_path if resolved_path.exists() else None

        if self.path is None:
            self.data = None
            return

        with self.path.open("rb") as f:
            self.data = tomllib.load(f)

    def get(self, *keys: str) -> Any | None:
        if self.data is None:
            return None

        value: Any = self.data

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]

        return value

    def require(self, *keys: str) -> Any:
        value = self.get(*keys)

        if value is None:
            raise KeyError(".".join(keys))

        return value
    # --- Raw Metadata Properties ---

    @property
    def name(self) -> str | None:
        """Raw [project.name] string from TOML."""
        return self.get("project", "name")

    # --- Resolved Naming Properties ---

    @property
    def app_name(self) -> str | None:
        if self.name:
            return to_kebab_case(self.name)

        if self.path is not None:
            return to_kebab_case(self.path.parent.name)

        return None

    @property
    def app_dir(self) -> Path | None:
        if self.app_name is None:
            return None

        path = Path.home() / f".{self.app_name}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def import_name(self) -> str | None:
        """Python module import name in snake_case (e.g. 'maxson_build_utils').

        Checks [tool.maxson-build-utils.names.import] first, falling back to
        snake_case(name).
        """
        custom_import = self.get(
            "tool",
            "maxson-build-utils",
            "names",
            "import",
        )

        if custom_import:
            return to_snake_case(custom_import)

        if self.name:
            return to_snake_case(self.name)

        if self.path is not None:
            return to_snake_case(self.path.parent.name)

        return None

    @property
    def pretty_name(self) -> str | None:
        """Human-readable project title (e.g. 'Maxson Build Utils').

        Checks [tool.maxson-build-utils.names.pretty] first, falling back to
        Title Case.
        """
        custom_pretty = self.get(
            "tool",
            "maxson-build-utils",
            "names",
            "pretty",
        )

        if custom_pretty:
            return custom_pretty

        if self.name:
            return to_title_case(self.name)

        if self.path is not None:
            return to_title_case(self.path.parent.name)

        return None

    @property
    def src_dir(self) -> Path | None:
        """Path to internal src module directory (e.g. project_root / 'src' / import_name)."""
        if self.path is None or self.import_name is None:
            return None

        return self.path.parent / "src" / self.import_name

    @property
    def data_dir(self) -> Path:
        """Path to internal data directory (e.g. project_root / 'src' / import_name / 'data' / )."""
        return self.src_dir / 'data'

    @property
    def icons_dir(self) -> Path:
        """Path to internal data directory (e.g. project_root / 'src' / import_name / 'data' / 'icons' )."""
        # only hardcode, or allow config pull in like 
        custom_icons_dir = self.get("tool", "maxson-build-utils", "icons", "dir")
        if custom_icons_dir:
            return self.path.parent / custom_icons_dir
        return self.data_dir / 'icons'

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
