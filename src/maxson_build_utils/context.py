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
        #proj = MaxsonPyProject(Path.cwd())
        return None
    return proj


def get_app_name() -> str:
    return APP_NAME or PACKAGE_DIR.name.replace("_", "-")

def get_pretty_name(app_name:str|None=None) -> str:
    if app_name is not None:
        return to_title_case(app_name)
    return to_title_case(PACKAGE_DIR.name)

def get_description() -> str:
    desc = get_pyproject().get("project", "description")
    if desc:
        return desc
    #return "Centralized build and packaging tools for the standard Maxson architecture." # no, don't hardcode
    return get_app_name()

def get_app_dir(app_name:str) -> Path:
    path = Path.home() / f".{app_name}"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_file_path(app_dir,app_name) -> Path | None:
    return app_dir / f"{app_name}_errors.log"


# Legacy module-level exports (safely computed via path fallbacks)
APP_NAME = "maxson-build-utils"
APP_NAME_PRETTY = "MaxsonBuildUtils"
DESCRIPTION_STR = get_description()
APP_DIR = get_app_dir(APP_NAME)
IMPORT_NAME = "maxson_build_utils"

LOG_FILE_PATH = get_log_file_path(APP_DIR,APP_NAME)
SRC_FOLDER_NAME = IMPORT_NAME
SERVICE = APP_NAME

CONFIG_PATH = APP_DIR / "config.json"
SECRET_PATH = APP_DIR / "vault.db"
ENV_PATH = PROJECT_ROOT / ".env"
