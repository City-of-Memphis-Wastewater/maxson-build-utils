# src/maxson_build_utils/scaffold_context.py
raw_context_str='''
# src/<app>/context.py
from __future__ import annotations
from pathlib import Path
from maxson_build_utils import PyProject 
from dworshak_config import DworshakConfig

pyproject=PyProject()
APP_NAME=pyproject.get("project","name")
SERVICE = APP_NAME # for dworshak basic ref
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True,exist_ok=True)
LOG_FILE_PATH = APP_DIR / f"{APP_NAME}_errors.log"
SRC_FOLDER_NAME = pyproject.get("tools","maxson-build-utils","names","import") # no vall the mbu function that falls back to snake case in names.py 
SRc_FOLDER
APP_NAME_PRETTY = pyproject.get("tools","maxson-build-utils","names","pretty")
config_mngr = DworshakConfig(path = APP_DIR / "config.json")
config_mngr.set(service=SERVICE,item="dummy",value=str(0))
'''

def init_context():

