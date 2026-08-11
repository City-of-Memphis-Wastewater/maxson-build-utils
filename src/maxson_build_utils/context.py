# src/maxson_build_utils/context.py
from __future__ import annotations
from pathlib import Path

APP_NAME = "maxson-build-utils"
SRC_FOLDER_NAME = "maxson_build_utils"
APP_NAME_PRETTY = "maxson-build-utils"
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True,exist_ok=True)
LOG_FILE_PATH = APP_DIR / f"{APP_NAME}_errors.log"

SERVICE = APP_NAME
DESCRIPTION_STR = "Centralized build and packaging tools for the standard Maxson architecture."

def get_config_mngr():
    from dworshak_config import DworshakConfig
    config_mngr = DworshakConfig(path = APP_DIR / "config.json")
    return config_mngr