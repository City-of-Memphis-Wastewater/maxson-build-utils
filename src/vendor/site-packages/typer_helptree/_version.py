#!/usr/bin/env python3 
# SPDX-License-Identifier: MIT
# src/typer_helptree/_version.py
from __future__ import annotations
import re
from pathlib import Path
import logging

# Setup a logger so the library can "whisper" errors without crashing the CLI
logger = logging.getLogger(__name__)

PACKAGE_NAME = "typer-helptree"

def get_version(package_name: str) -> str:
    # 1. Try the official way (Installed/Production)
    try:
        from importlib.metadata import version
        return version(package_name)
    except Exception:
        pass

    # 2. Try the dev/zip way (Local/PyZ)
    try:
        return (Path(__file__).parent / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0-unknown"
    
__version__ = get_version(PACKAGE_NAME)
