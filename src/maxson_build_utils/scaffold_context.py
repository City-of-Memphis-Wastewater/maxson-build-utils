# src/maxson_build_utils/scaffold_context.py
from __future__ import annotations
from .helpers import write_str_to_file
from .names import get_src_dir, get_src_name
def run_init_context( ):
    write_str_to_file(path= get_src_dir() / "context.py", text = raw_context_str)
raw_context_str=f'''
# src/{get_src_name()}/context.py
from __future__ import annotations
from pathlib import Path
from maxson_build_utils import PyProject 
from dworshak_config import DworshakConfig
from maxson_build_utils.names import get_src_dir, get_pretty_name, get_app_name

pyproject=PyProject()

APP_NAME = get_app_name()
SERVICE = APP_NAME
DESCRIPTION_STR = pyproject.get("project","description")
SRC_FOLDER_NAME = get_src_dir()
APP_NAME_PRETTY = get_pretty_name()
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True,exist_ok=True)
LOG_FILE_PATH = APP_DIR / f"{APP_NAME}_errors.log"

config_mngr = DworshakConfig(path = APP_DIR / "config.json")
config_mngr.set(service=SERVICE,item="dummy",value=str(0))
'''
