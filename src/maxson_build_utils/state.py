# src/maxson_build_utils/state.py
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .config import get_config_mngr, get_env_mngr

def export_build_env_vars(app_filepath: Path, executable_descriptor: str) -> None:
    """Exports dynamic PyInstaller paths to os.environ and GitHub Actions runner state."""
    logger.debug("export_build_env_vars()")

    # persisitent var storage to disk
    config_mngr = get_config_mngr() # assumes maxson-build-utils, which is fine, but we don't need projects overwriting others
    config_mngr.set(service="temp", item="app_filepath",value=str(app_filepath),overwrite=True)
    config_mngr.set(service="temp", item="executable_descriptor",value=executable_descriptor,overwrite=True)

    # pesisitent storage to disk in CWD
    env_mngr = get_env_mngr()
    env_mngr.set(key="temp-app-filepath",value=str(app_filepath),overwrite=True)
    env_mngr.set(key="temp-executable-descriptor",value=executable_descriptor,overwrite=True)
    
    
def get_executable_descriptor()->str:
    #config_mngr = get_config_mngr()
    #return config_mngr.get(service="temp", item="executable_descriptor")
    env_mngr = get_env_mngr()
    return env_mngr.get(key="temp-executable-descriptor")
    
def get_pyinstaller_onedir_export_entrypoint_path()->Path:
    #config_mngr = get_config_mngr("")
    #app_filepath = config_mngr.get(service="temp", item="app_filepath")
    env_mngr = get_env_mngr()
    app_filepath =  env_mngr.get(key="temp-app-filepath")   
    return Path(app_filepath).expanduser().resolve()
