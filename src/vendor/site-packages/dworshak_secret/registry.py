# src/dworshak_secret/registry.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import os

from .paths import KEY_REGISTRY_FILE

def load_key_registry() -> dict:
    if not KEY_REGISTRY_FILE.exists():
        return {}
    try:
        return json.loads(KEY_REGISTRY_FILE.read_text())
    except json.JSONDecodeError:
        return {}

def save_key_registry(data: dict):
    KEY_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_REGISTRY_FILE.write_text(json.dumps(data, indent=2))
    # Standard dworshak permission safety
    from .paths import ensure_secure_permissions
    ensure_secure_permissions(KEY_REGISTRY_FILE)

def register_vault_key(db_path: Path | str, metadata: dict):
    """Generic registration for any vault-related metadata."""
    
    registry = load_key_registry()
    path_key = str(Path(db_path).resolve())
    
    current_entry = registry.get(path_key, {})
    current_entry.update(metadata)
    current_entry["time_registered"] = datetime.now().isoformat()
    
    registry[path_key] = current_entry
    save_key_registry(registry)

def unregister_vault_key(db_path: Path | str) -> bool:
    """Remove a vault's entry from the registry if it exists."""
    registry = load_key_registry()
    path_key = str(Path(db_path).resolve())
    
    if path_key in registry:
        del registry[path_key]
        save_key_registry(registry)
        return True
    return False

def get_registered_key(db_path: Path | str) -> Path | None:
    """Retrieve the key path for a specific vault."""
    registry = load_key_registry()
    path_key = str(Path(db_path).resolve())
    entry = registry.get(path_key)

    if not entry or "key_path" not in entry:
        return None

    key_path = Path(entry["key_path"])

    if not key_path.is_absolute():
        key_path = Path(db_path).parent / key_path

    return key_path.resolve()


