# src/maxson-build-utils/config.py
from __future__ import annotations
from pathlib import Path

def get_config_mngr():
    from .context import CONFIG_PATH
    from dworshak_config import DworshakConfig
    return DworshakConfig(path=CONFIG_PATH)

def get_persistence_mngr():
    from dworshak_env import DworshakEnv
    filename = ".persist"
    filepath = Path.cwd() / filename
    return DworshakEnv(filepath)