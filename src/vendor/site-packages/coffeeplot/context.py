# src/coffeeplot/context.py
from __future__ import annotations
from pathlib import Path
from dworshak_config import DworshakConfig

APP_NAME = "coffeeplot"
APP_DIR = Path.home() / f".{APP_NAME}"
EXPORT_DIR = APP_DIR / "export"
DATABASE_DIR = APP_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

config_mngr = DworshakConfig(path=APP_DIR / "config.json")
config_mngr.set(service=APP_NAME,item="null",value="null")
