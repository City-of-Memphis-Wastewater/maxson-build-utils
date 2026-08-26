# src/maxson_build_utils/context.py
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from .pyproject import MaxsonPyProject
from .names import to_title_case, to_kebab_case, to_snake_case

# Fixed physical paths anchored strictly to this file's installation location
PACKAGE_DIR = Path(__file__).resolve().parent          # .../src/maxson_build_utils
SRC_DIR = PACKAGE_DIR.parent                             # .../src
PROJECT_ROOT = SRC_DIR.parent                            # .../maxson-build-utils


@lru_cache(maxsize=1)
def get_pyproject() -> MaxsonPyProject:
    """Parses pyproject.toml lazily from project root or working directory."""
    proj = MaxsonPyProject(PROJECT_ROOT)
    if proj.path is None:
        proj = MaxsonPyProject(Path.cwd())
    return proj


def get_app_name() -> str:
    return get_pyproject().app_name or PACKAGE_DIR.name.replace("_", "-")

def get_pretty_name() -> str:
    proj = get_pyproject()
    if proj.pretty_name:
        return proj.pretty_name
    return to_title_case(PACKAGE_DIR.name)

def get_import_name() -> str:
    return get_pyproject().import_name or PACKAGE_DIR.name

def get_description() -> str:
    desc = get_pyproject().get("project", "description")
    if desc:
        return desc
    #return "Centralized build and packaging tools for the standard Maxson architecture." # no, don't hardcode
    return get_app_name()

def get_app_dir() -> Path:
    proj = get_pyproject()
    if proj.app_dir is not None:
        return proj.app_dir
    
    path = Path.home() / f".{get_app_name()}"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_file_path() -> Path | None:
    proj = get_pyproject()
    if proj.log_file_path is not None:
        return proj.log_file_path
    
    # Fallback to standard OS cache path if app_dir cannot be created
    app_name = get_app_name()
    return Path.home() / ".cache" / app_name / f"{app_name}_errors.log"


# Legacy module-level exports (safely computed via path fallbacks)
APP_NAME = get_app_name()
APP_NAME_PRETTY = get_pretty_name()
IMPORT_NAME = get_import_name()
SRC_FOLDER_NAME = IMPORT_NAME
DESCRIPTION_STR = get_description()
APP_DIR = get_app_dir()
LOG_FILE_PATH = get_log_file_path()
SERVICE = APP_NAME

CONFIG_PATH = APP_DIR / "config.json"
SECRET_PATH = APP_DIR / "vault.db"
ENV_PATH = Path.cwd() / ".env"
