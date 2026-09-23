# src/dworshak_access/vault.py
from __future__ import annotations
import sqlite3
import os
import stat
from pathlib import Path
from typing import NamedTuple
from enum import IntEnum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

from .paths import DB_FILE, resolve_key_path_for_db, ensure_secure_permissions

CURRENT_TOOL_SCHEMA_VERSION = 2

class VaultCode(IntEnum):
    DIR_MISSING = 0
    DB_MISSING = 1
    DB_FILE_HEALTHY_WITH_RW_WARNINGS = 2
    HEALTHY = 3
    DB_CORRUPTED = 4
    #KEY_MISSING = 5 # defunct, key not check in vault status

class KeyCode(IntEnum):
    KEY_FILE_MISSING = 0
    KEY_FILE_NOT_PLAINTEXT_STR = 1
    KEY_FILE_HEALTHY_WITH_RW_WARNINGS = 2
    HEALTHY = 3

class VaultStatus(NamedTuple):
    is_valid: bool
    message: str
    root_path: Path
    rw_code: int | None
    health_code: int
    vault_db_version: int

class KeyStatus(NamedTuple):
    is_valid: bool
    message: str
    key_path: Path
    rw_code: int | None
    health_code: int

@dataclass
class VaultResponse:
    success: bool
    message: str
    is_new: bool = False

def initialize_vault(db_path, key_path,force:bool=False)->VaultResponse:
    from .key import create_vault_key
    # 1. Check if the DB exists and has a schema already
    pre_res = _initialize_vault_pre_key(db_path)
    
    # 2. If the vault DB already exists, don't try to overwrite or re-key
    if not force and not pre_res.is_new:
        return VaultResponse(
            success=False, 
            message="Vault database already exists. Aborting to prevent accidental overwrite.", 
            is_new=False
        )
    
    #vault_key = create_vault_key(db_path, key_path)
    create_vault_key(db_path, key_path)
    return VaultResponse(success=True, message="Fresh vault created and corresponding fresh key created.", is_new=True)

def force_initialize_vault(db_path, key_path)->VaultResponse:
    return initialize_vault(db_path, key_path, force=True)
        
def _initialize_vault_pre_key(
        db_path: Path | str | None = None
        ) -> VaultResponse:
    """Infrastructure setup: ensures directories and base schema exist."""
    #from .security import get_fernet

    db_path = Path(db_path) if db_path else DB_FILE
    db_path.parent.mkdir(parents=True, exist_ok=True)
    #get_fernet(db_path,key_path)

    conn = sqlite3.connect(db_path)
    try:
        existing_version = conn.execute("PRAGMA user_version").fetchone()[0]
        logger.debug(f"dworshak-secret database existing_version = {existing_version}")
        if existing_version == 0:
            _create_base_schema(conn)
            conn.execute(f"PRAGMA user_version = {CURRENT_TOOL_SCHEMA_VERSION}")
            conn.commit()
            return VaultResponse(success=True, message="New vault initialized.", is_new=True)
        return VaultResponse(success=True, message="Vault verified.", is_new=False)
    finally:
        conn.close()

def ensure_vault(db_path):
    status = check_vault(db_path)
    if not status.is_valid:
        raise RuntimeError(status.message)

def check_vault(
    db_path: Path | str | None = None, 
    ) -> VaultStatus:
    """The source of truth for vault health."""

    db_path = Path(db_path) if db_path else DB_FILE
    vault_root = db_path.parent

    if not vault_root.exists():
        return VaultStatus(
            False, 
            f"Vault directory missing: {vault_root}",
            vault_root, 
            None, 
            VaultCode.DIR_MISSING, 
            CURRENT_TOOL_SCHEMA_VERSION
        )

    if not db_path.exists():
        return VaultStatus(
            is_valid = False, 
            message = f"Vault DB missing: {db_path.name}", 
            root_path = vault_root, 
            rw_code = None, 
            health_code = VaultCode.DB_MISSING, 
            vault_db_version = CURRENT_TOOL_SCHEMA_VERSION
        )

    
    if is_db_corrupted(db_path):
        return VaultStatus(
            False, 
            "Vault DB corrupted", 
            vault_root, 
            _get_rw_mode(db_path), 
            VaultCode.DB_CORRUPTED, 
            CURRENT_TOOL_SCHEMA_VERSION
        )
    
    # Permission checks for non-Windows
    warnings = []
    if os.name != "nt":
        if not _is_600(db_path): warnings.append("vault.db permissions not 600")

    if warnings:
        return VaultStatus(
            True, 
            f"Healthy (warnings: {'; '.join(warnings)})", 
            vault_root, 
            _get_rw_mode(db_path), 
            VaultCode.DB_FILE_HEALTHY_WITH_RW_WARNINGS, 
            CURRENT_TOOL_SCHEMA_VERSION
        )

    return VaultStatus(
        True, 
        "Vault healthy", 
        vault_root, 
        _get_rw_mode(db_path), 
        VaultCode.HEALTHY, 
        CURRENT_TOOL_SCHEMA_VERSION
    )

def check_key_file(
    key_path: Path | str | None = None,
    ) -> KeyStatus:
    """The source of truth for key health."""
    from .paths import ensure_secure_permissions
    # Logic: Key check
    if not key_path.exists():
        return KeyStatus(
            is_valid = False, # True, changed June 2026 
            message = "Key missing/Crypto unavailable", 
            key_path = key_path, 
            rw_code = _get_rw_mode(key_path), 
            health_code = KeyCode.KEY_FILE_MISSING
        )
    # ---

    
    # Permission checks for non-Windows
    warnings = []
    if os.name != "nt":
        if not _is_600(key_path): warnings.append(".key permissions not 600")

    if warnings:
        return KeyStatus(
            is_valid = True, 
            message = f"Healthy (warnings: {'; '.join(warnings)})", 
            key_path = key_path, 
            rw_code = _get_rw_mode(key_path), 
            health_code = KeyCode.KEY_FILE_HEALTHY_WITH_RW_WARNINGS, 
        )

    return KeyStatus(
        is_valid = True, 
        message = "Key healthy", 
        key_path = key_path, 
        rw_code = _get_rw_mode(key_path), 
        health_code = KeyCode.HEALTHY
    )

def heal_vault_file(db_path: Path):
    # Self-healing if requested
    ensure_secure_permissions(db_path)

def heal_key_file(key_path: Path):
    # Self-healing if requested
    ensure_secure_permissions(key_path)
    

def is_db_corrupted(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return result != "ok"
    finally:
        conn.close()

def _create_base_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            encrypted_secret BLOB NOT NULL,
            PRIMARY KEY(service, item)
        )
    """)

def _get_rw_mode(path: Path) -> int | None:
    try: return stat.S_IMODE(path.stat().st_mode)
    except Exception: return None

def _is_600(path: Path) -> bool:
    return _get_rw_mode(path) == 0o600
