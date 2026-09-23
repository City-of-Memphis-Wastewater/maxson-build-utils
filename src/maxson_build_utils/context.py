# src/maxson_build_utils/context.py

from __future__ import annotations

from pathlib import Path

from .names import to_title_case


# Physical location of maxson-build-utils itself.
PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
PROJECT_ROOT_DIR = PROJECT_ROOT

APP_NAME = "maxson-build-utils"
APP_NAME_PRETTY = "MaxsonBuildUtils"
IMPORT_NAME = "maxson_build_utils"
SRC_FOLDER_NAME = IMPORT_NAME
SERVICE = APP_NAME
DESCRIPTION_STR = "A convention-optional build and deployment framework, with an opinionated Maxson project scaffold available as a convenience."

def get_app_name() -> str:
    return APP_NAME


def get_pretty_name(app_name: str | None = None) -> str:
    if app_name is not None:
        return to_title_case(app_name)

    return APP_NAME_PRETTY


def get_app_dir(app_name: str) -> Path:
    path = Path.home() / f".{app_name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


APP_DIR = get_app_dir(APP_NAME)

LOG_FILE_PATH = APP_DIR / f"{APP_NAME}_errors.log"

CONFIG_PATH = APP_DIR / "config.json"
SECRET_PATH = APP_DIR / "vault.db"
ENV_PATH = PROJECT_ROOT / ".env"
