# src/maxson_build_utils/pyproject.py
from __future__ import annotations

from pathlib import Path
from typing import Any,List
import json
import logging
logger = logging.getLogger(__name__)

from .names import to_snake_case, to_kebab_case, to_title_case
from .entry import get_cli_entry_point
from .config import get_persistence_mngr
from .state import set_description_to_disk

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
    def new_src_dir_new(self) -> Path | None:
        """Path to the source container directory (e.g. project_root / 'src')."""
        if self.root_dir is None:
            return None
        return self.root_dir / "src"

    @property
    def version_file(self) -> Path | None:
        """Path to src/<import_name>/VERSION."""
        if self.package_dir is None:
            return None
        return self.package_dir / "VERSION"


    @property
    def version(self) -> str:
        """Return the PEP 621 project version."""
        version = self.get("project", "version")

        if version is None or not str(version).strip():
            raise ValueError(
                f"Project version is missing from {self.path}. "
                "Define [project.version] in pyproject.toml."
            )

        return str(version).strip()
        
class MaxsonPyProject(PyProject):
    """PyProject with Maxson architecture conventions."""

    # --- Override properties ---
    @property
    def version(self) -> str:
        """Return the project version using Maxson conventions."""
        vf = self.version_file

        if vf is not None and vf.is_file():
            version = vf.read_text(encoding="utf-8").strip()
            if version:
                return version

        return super().version
        
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
            set_description_to_disk(description_str=project_description)
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

    # --- Path resolution ---
    @property
    def src_dir_defunct(self) -> Path | None:
        """Path to internal src module directory (e.g. project_root / 'src' / import_name)."""
        if self.path is None or self.import_name is None:
            return None

        return self.root_dir / "src" / self.import_name

    @property
    def package_dir(self) -> Path | None:
        """Path to the package directory containing __init__.py (e.g. project_root / 'src' / import_name)."""
        if self.package_dir is None or self.import_name is None:
            return None
        return self.package_dir / self.import_name

    @property
    def data_dir(self) -> Path | None:
        """Path to internal data directory (e.g. project_root / 'src' / import_name / 'data' / )."""
        if self.package_dir is None:
            return None

        return self.package_dir / "data"


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
    def entry_point(self) -> str | None:
        """Return the primary CLI entry point.

        Uses the first [project.scripts] entry when defined.
        Falls back to the standard Maxson __main__:app convention.
        """
        scripts = self.get("project", "scripts")

        if isinstance(scripts, dict) and scripts:
            return str(next(iter(scripts.values())))

        if self.import_name is None:
            return None

        return get_cli_entry_point(self.import_name)

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

    @property
    def pyinstaller_config(self) -> dict[str, Any]:
        """Returns the [tool.maxson-build-utils.pyinstaller] section."""
        return self.get("tool", "maxson-build-utils", "pyinstaller") or {}

    @property
    def pyinstaller_spec_file(self) -> Path | None:
        """Path to packaging/pyinstaller/<import_name>.spec."""
        if self.root_dir is None or self.import_name is None:
            return None
        return self.root_dir / "packaging" / "pyinstaller" / f"{self.import_name}.spec"

    @property
    def icon_ico_path(self) -> Path | None:
        """Resolves .ico path from [tool.maxson-build-utils.icons]."""
        ico_rel = self.get("tool", "maxson-build-utils", "icons", "ico-256", "path")
        if ico_rel and self.root_dir:
            p = self.root_dir / ico_rel
            return p if p.exists() else None
        return None

    @property
    def icon_icns_path(self) -> Path | None:
        """Resolves .icns path from [tool.maxson-build-utils.icons]."""
        icns_rel = self.get("tool", "maxson-build-utils", "icons", "icns", "path")
        if icns_rel and self.root_dir:
            p = self.root_dir / icns_rel
            return p if p.exists() else None
        return None
# ---

def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    return str(value)
