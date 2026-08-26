# src/maxson-build-utils/config.py
from __future__ import annotations

def get_config_mngr():
    from .context import APP_DIR, CONFIG_PATH
    from dworshak_config import DworshakConfig
    return DworshakConfig(path=CONFIG_PATH)
