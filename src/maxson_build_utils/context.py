# src/maxson_build_utils/context.py
from __future__ import annotations
from pathlib import Path

APP_NAME = "maxson-build-utils"
SRC_FOLDER_NAME = "maxson_build_utils"
APP_NAME_PRETTY = "maxson-build-utils"
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True,exist_ok=True)

SERVICE = APP_NAME
DESCRIPTION_STR = "Centralized build tools for the standard Maxson architecture."

def get_config_mngr():
    from dworshak_config import DworshakConfig
    config_mngr = DworshakConfig(path = APP_DIR / "config.json")
    config_mngr.set(service=APP_NAME, item="dummy",value="null",overwrite=False)
