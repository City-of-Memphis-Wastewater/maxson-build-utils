# src/maxson_build_utils/context.py
from __future__ import annotations
from pathlib import Path

from .pyproject import PyProject
_pyproject = PyProject()

APP_NAME = _pyproject.app_name
#APP_NAME_PRETTY = _pyproject.pretty_name
#IMPORT_NAME = _pyproject.import_name
#SRC_DIR = _pyproject.src_dir
#SRC_FOLDER_NAME = IMPORT_NAME
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True,exist_ok=True)

SERVICE = APP_NAME
DESCRIPTION_STR = "Centralized build and packaging tools for the standard Maxson architecture."

def get_config_mngr():
    from dworshak_config import DworshakConfig
    config_mngr = DworshakConfig(path = APP_DIR / "config.json")
    return config_mngr

