# src/maxson_build_utils/state.py
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .config import get_config_mngr
from .context import APP_NAME

def export_build_env_vars(app_filepath: Path, executable_descriptor: str) -> None:
    """Exports dynamic PyInstaller paths to os.environ and GitHub Actions runner state."""
    logger.debug("export_build_env_vars()")

    # persisitent var storage to disk
    config_mngr = get_config_mngr()
    config_mngr.set(service=APP_NAME, item="app_filepath",value=str(app_filepath),overwrite=True)
    config_mngr.set(service=APP_NAME, item="executable_descriptor",value=executable_descriptor,overwrite=True)
    
def get_executable_descriptor()->str:
    config_mngr = get_config_mngr()
    return config_mngr.get(service=APP_NAME, item="executable_descriptor")

def get_pyinstaller_onedir_exe_filepath()->Path:
    config_mngr = get_config_mngr()
    app_filepath = config_mngr.get(service=APP_NAME, item="app_filepath")
    return Path(app_filepath).expanduser().resolve()
