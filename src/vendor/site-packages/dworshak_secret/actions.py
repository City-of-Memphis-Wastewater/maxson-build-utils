# src/dworshak_access/actions.py
from __future__ import annotations
import sqlite3
import json
import datetime
import shutil
import sys
import os
from pathlib import Path
from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .core import DworshakSecret

from .paths import (
    DB_FILE, 
    get_default_export_path, 
    ensure_secure_permissions, 
    get_backup_path,
    resolve_key_path_for_db
)
from . import vault

def export_vault(
    db_path: Path | str | None = None,
    key_path: Path | str | None = None,
    output_path: Path | str | None = None,
    decrypt: bool = False,
    yes: bool = False
) -> str | None:
    """Orchestrates a full vault export with metadata."""

    if db_path and str(db_path) == ":memory:":
        return None

    db_path = Path(db_path) if db_path else DB_FILE
    if not db_path.exists():
        return None

    key_path = resolve_key_path_for_db(db_path, key_path)
    
    if output_path is None:
        output_path = get_default_export_path()
    output_path = Path(output_path)

    status = vault.check_vault(db_path,key_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # These extraction helpers remain in vault.py as they are low-level DB I/O
        if decrypt and yes:
            # We construct a transient manager context cleanly here for the standalone execution
            from .core import DworshakSecret
            mngr = DworshakSecret(db_path=db_path, key_path=key_path)
            table_data = _fill_db_dump_decrypted(conn, client=mngr)
        else:
            table_data = _fill_db_dump_encrypted(conn)

        export_package = {
            "metadata": {
                "export_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "decrypted": decrypt,
                "vault_schema_version": status.vault_db_version,
                "dworshak_tool_schema_version": vault.CURRENT_TOOL_SCHEMA_VERSION,
            },
            "tables": table_data
        }

        with open(output_path, "w") as f:
            json.dump(export_package, f, indent=4)

        if os.name != "nt":
            output_path.chmod(0o600)

        return str(output_path)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return None
    finally:
        conn.close()

def import_records(
    client: DworshakSecret,
    json_path: Path | str,
    overwrite: bool = False
) -> dict | None:
    """Merges records from JSON. Triggers safety backup if overwriting."""
    
    if json_path is None:
        return {}
    
    json_path = Path(json_path)
    with open(json_path, "r") as f:
        data = json.load(f)

    if not _validate_import_meta(data.get("metadata", {})):
        return None

    creds = data.get("tables", {}).get("credentials", [])
    
    # 1. Safety Check: If we are overwriting, backup the DB first
    overlap = _get_overlap(creds, client)
    if overlap and overwrite:
        if client.db_path and str(client.db_path) != ":memory:":
            _trigger_safety_backup(Path(client.db_path))

    # 2. Process records
    stats = {"added": 0, "updated": 0, "skipped": 0}
    for row in creds:
        service, item = row.get("service"), row.get("item")
        secret = row.get("encrypted_secret")

        if not (service and item and secret):
            continue

        existing = client.get(service, item)
        if existing is None:
            client.set(service, item, secret)
            stats["added"] += 1
        elif overwrite:
            client.set(service, item, secret)
            stats["updated"] += 1
        else:
            stats["skipped"] += 1

    return stats

def backup_vault(
    db_path: Path | str | None = None,
    extra_suffix: str = "",
    include_timestamp: bool = True,
    dest_dir: Path | str | None = None,
) -> Path | None:
    """Creates a secured copy of the database."""
    if db_path and str(db_path) == ":memory:":
        return None

    db_path = Path(db_path) if db_path else DB_FILE
    if not db_path.exists():
        return None

    backup_path = get_backup_path(
        extra_suffix=extra_suffix,
        dest_dir=dest_dir,
        include_timestamp=include_timestamp,
    )

    try:
        shutil.copy2(db_path, backup_path)
        ensure_secure_permissions(backup_path)
        return backup_path
    except Exception:
        return None

# --- Internal Action Helpers ---

def _validate_import_meta(meta: dict) -> bool:
    if not meta.get("decrypted"):
        logger.error("Import Rejected: JSON must be a decrypted export.")
        return False
    return True

def _get_overlap(incoming_creds: list, client: DworshakSecret) -> set[tuple[str, str]]:
    incoming_keys = {
        (row['service'], row['item']) 
        for row in incoming_creds 
        if 'service' in row and 'item' in row
    }
    existing_keys = set(client.list_contents())
    return incoming_keys.intersection(existing_keys)

def _trigger_safety_backup(db_path: Path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(f".db.bak_{timestamp}")
    shutil.copy2(db_path, backup_path)
    logger.debug(f"Safety backup created: {backup_path.name}")
    return backup_path

# --- Low Level Data Extractors (Used by actions.py) ---

def _fill_db_dump_encrypted(conn: sqlite3.Connection) -> dict:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    db_dump = {}
    for table in tables:
        t_name = table[0]
        cursor = conn.execute(f"SELECT * FROM {t_name}")
        db_dump[t_name] = [
            {k: (v.hex() if isinstance(v, bytes) else v) for k, v in dict(row).items()}
            for row in cursor.fetchall()
        ]
    return db_dump

def _fill_db_dump_decrypted(
        conn: sqlite3.Connection, 
        client: DworshakSecret
    ) -> dict:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    db_dump = {}
    
    for table in tables:
        t_name = table[0]
        cursor = conn.execute(f"SELECT * FROM {t_name}")
        rows = [dict(row) for row in cursor.fetchall()]
        
        for row in rows:
            if "service" in row and "item" in row:
                try:
                    row["encrypted_secret"] = client.get(row["service"], row["item"])
                except Exception:
                    row["encrypted_secret"] = "DECRYPTION_FAILED"
            
            for k, v in row.items():
                if isinstance(v, bytes): row[k] = v.hex()
        db_dump[t_name] = rows
    return db_dump
