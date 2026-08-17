# src/maxson_build_utils/scaffold/context.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file

def run_init_context(root_dir: Path | str | None = None) -> None:
    from ..pyproject import PyProject 
    pyproject = PyProject(root_dir)

    raw_context_str='''
# src/__IMPORT_NAME__/context.py
from __future__ import annotations
from pathlib import Path
from maxson_build_utils import PyProject 
from dworshak_config import DworshakConfig

_pyproject = PyProject()

APP_NAME = _pyproject.app_name
APP_NAME_PRETTY = _pyproject.pretty_name
IMPORT_NAME = _pyproject.import_name
SRC_DIR = _pyproject.src_dir
SRC_FOLDER_NAME = IMPORT_NAME
SERVICE = APP_NAME
DESCRIPTION_STR = _pyproject.get("project","description")
APP_DIR = _pyproject.app_dir
LOG_FILE_PATH = _pyproject.log_file_path

config_mngr = DworshakConfig(path = APP_DIR / "config.json")
config_mngr.set(service=SERVICE,item="dummy",value=str(0))
'''
    raw_context_str = raw_context_str.replace("__IMPORT_NAME__", pyproject.import_name)
    write_str_to_file(pyproject.src_dir / "context.py", text = raw_context_str)
