# src/dworshak_secret/legacy.py
from __future__ import annotations
from pathlib import Path
from typing import List

from .core import DworshakSecret

# --- Legacy Functional API (Compatibility Layer) ---

def get_secret(service: str, item: str, fail: bool = False, db_path: Path | str | None = None) -> str | None:
    return DworshakSecret(db_path).get(service, item, fail=fail)

def store_secret(service: str, item: str, secret: str, overwrite: bool = True, db_path: Path | str | None = None):
    return DworshakSecret(db_path).set(service = service, item = item, value = secret, overwrite=overwrite, fernet=None)

def list_credentials(db_path: Path | str | None = None) -> List[tuple[str, str]]:
    return DworshakSecret(db_path).list_contents()

def remove_secret(service: str, item: str, db_path: Path | str | None = None) -> bool:
    return DworshakSecret(db_path).remove(service, item)
