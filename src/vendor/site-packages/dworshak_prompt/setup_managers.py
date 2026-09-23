# src/dworshak_prompt/setup_managers.py

from __future__ import annotations
from pathlib import Path

def setup_dworshak_managers(dir:str|Path|None=None):
    """
    A limited but basic approach for setting up client class instances.
    Key file for an encrypted database vault will be automatically assessed and is not indicated here.
    """
    from dworshak_env import DworshakEnv
    from dworshak_config import DworshakConfig
    from dworshak_secret import DworshakSecret
    from dworshak_prompt import Obtain

    env_mngr = DworshakEnv() # assume this stays in CWD. If the user wants a custom path, they'll have to do it manually and not use setup_dworshak().

    resolved_dir = dir if dir is not None else env_mngr.get("DWORSHAK_DIR")
    if resolved_dir:
        resolved_dir = Path(resolved_dir).expanduser().resolve()
        config_path = resolved_dir / "config.json"
        secret_path = resolved_dir / "vault.db"
    else:
        # let the defaults hit
        config_path = None
        secret_path = None


    config_mngr = DworshakConfig(path = config_path)
    secret_mngr = DworshakSecret(db_path = secret_path)
    obtain_mngr = Obtain(secret_path=secret_path, config_path = config_path)

    dworshak_managers = {
        "root": resolved_dir,
        "env":env_mngr, 
        "config":config_mngr, 
        "secret":secret_mngr, 
        "obtain":obtain_mngr
    } 
    return dworshak_managers
