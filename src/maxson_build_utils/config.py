# src/maxson-build-utils/config.py
from __future__ import annotations
from .pyproject import PyProject

_pyproject = PyProject()

def get_config_mngr():
    from dworshak_config import DworshakConfig
    if _pyproject.config_path is None:
        return None

    return DworshakConfig(path=_pyproject.config_path)
