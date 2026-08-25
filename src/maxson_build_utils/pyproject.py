# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any,List
import json
import logging
logger = logging.getLogger(__name__)

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
    def name(self) -> str:
        """Raw [project.name] string from TOML, defaulting to the project directory name."""
        project_name = self.get("project", "name")
        if project_name is not None:
            return project_name

        if self.root_dir is not None:
            return self.root_dir.name

        return Path.cwd().name

    @property
    def root_dir(self) -> Path | None:
        """Path to module directory root (e.g. project_root )."""
        if self.path is None:
            return None

        return self.path.parent

    @property
    def version_file(self) -> Path | None:
        """Path to src/<import_name>/VERSION."""
        if self.src_dir is None:
            return None
        return self.src_dir / "VERSION"

    @property
    def version(self) -> str:
        """Dynamically read version from src/<import_name>/VERSION.
        
        Falls back to [project.version] in pyproject.toml if VERSION file doesn't exist.
        """
        vf = self.version_file
        if vf is not None and vf.is_file():
            ver = vf.read_text(encoding="utf-8").strip()
            if ver:
                return ver

        # Fallback to pyproject.toml [project.version]
        toml_ver = self.get("project", "version")
        if toml_ver:
            return str(toml_ver).strip()

        return "0.1.0"

class MaxsonPyProject(PyProject):
    """PyProject with Maxson architecture conventions."""

    # --- Resolved Naming Properties ---

    @property
    def app_name(self) -> str | None:
        if self.name:
            return to_kebab_case(self.name)

        target_dir = self.path.parent if self.path is not None else Path.cwd()
        return to_kebab_case(target_dir.name)

    @property
    def description(self) -> str | None:
        project_description = self.get("project", "description")
        if project_description is not None:
            return project_description
        else:
            return ""
    
    @property
    def app_dir(self) -> Path | None:
        configured = self._configured_path("app_dir")

        if configured is not None:
            configured.mkdir(parents=True, exist_ok=True)
            return configured

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

    # --- Path resolution ---
    @property
    def src_dir(self) -> Path | None:
        """Path to internal src module directory (e.g. project_root / 'src' / import_name)."""
        if self.path is None or self.import_name is None:
            return None

        return self.root_dir / "src" / self.import_name

    @property
    def data_dir(self) -> Path | None:
        """Path to internal data directory (e.g. project_root / 'src' / import_name / 'data' / )."""
        if self.src_dir is None:
            return None

        return self.src_dir / "data"


    @property
    def icons_dir(self) -> Path | None:
        """Path to internal data directory (e.g. project_root / 'src' / import_name / 'data' / 'icons' )."""
        if self.data_dir is None:
            return None

        return self.data_dir / "icons"

    @property
    def log_file_path(self) -> Path | None:
        configured = self._configured_path("log_file")

        if configured is not None:
            return configured

        if self.app_dir is None or self.app_name is None:
            return None

        return self.app_dir / f"{self.app_name}_errors.log"

    @property
    def author(self) -> str | None:
        """Extract primary author or maintainer string from PEP 621 metadata."""
        authors = self.get("project", "authors")
        if isinstance(authors, list) and authors:
            first = authors[0]
            if isinstance(first, dict):
                name = first.get("name", "")
                email = first.get("email", "")
                if name and email:
                    return f"{name} <{email}>"
                return name or email or None
            if isinstance(first, str):
                return first

        # Fallback to direct string/dict if defined under author
        author = self.get("project", "author")
        if isinstance(author, dict):
            name = author.get("name", "")
            email = author.get("email", "")
            if name and email:
                return f"{name} <{email}>"
            return name or email or None
        if isinstance(author, str):
            return author

        return None

    def _configured_path(self, *keys: str) -> Path | None:
        value = self.get(
            "tool",
            "maxson-build-utils",
            "paths",
            *keys,
        )

        if value is None or self.path is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"Configured path {'.'.join(keys)!r} must be a string"
            )

        return self.path.parent / value


# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
