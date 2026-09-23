from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional, Any
import sys
import logging

from .paths import DB_FILE, KEY_FILE
from .vault import initialize_vault, ensure_vault, check_vault, check_key_file

class DworshakSecret:
    """
    Stateless client wrapper over a persistent vault.

    Lifecycle is external:
        - initialize_vault() → creates vault + key
        - ensure_vault() → validates only
        - get/set/remove → require existing vault
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        key_path: Path | str | None = None,
        crypto_backend: Any | None = None,
    ):
        self.db_path = (
            Path(db_path).expanduser().resolve() 
            if db_path 
            else DB_FILE
        )
        self._key_path_override = (
            Path(key_path).expanduser().resolve() 
            if key_path 
            else None
        )
        self._resolved_key_path: Path | None = None
        # IMPORTANT: do NOT initialize crypto here
        self._crypto_backend = crypto_backend

    # ----------------------------
    # Path resolution
    # ----------------------------

    def resolve_key_path(self) -> Path:
        if self._resolved_key_path:
            return self._resolved_key_path
        from .paths import resolve_key_path_for_db
        self._resolved_key_path = resolve_key_path_for_db(self.db_path, self._key_path_override)
        logging.debug(f"Resolved key_path: {self._resolved_key_path}")
        return self._resolved_key_path

    # ----------------------------
    # Lazy crypto backend
    # ----------------------------

    @property
    def crypto_backend(self):
        if self._crypto_backend:
            return self._crypto_backend

        from .crypto.fernet import FernetBackend
        from .key import load_current_key
        key_path = self.resolve_key_path()
        
        key_bytes = load_current_key(key_path=key_path)
        self._crypto_backend = FernetBackend(key_bytes.decode('utf-8'))
        
        #key_str = get_key_str_from_key_path(key_path=key_path)
        #self._crypto_backend = FernetBackend(key_str = key_str)
        return self._crypto_backend

    # ----------------------------
    # Vault lifecycle wrappers
    # ----------------------------

    def initialize_vault(self, **kwargs):
        return initialize_vault(
            db_path=self.db_path,
            key_path=self.resolve_key_path(),
            **kwargs
        )

    def ensure_vault_or_raise(self):
        return ensure_vault(
            db_path=self.db_path,
        )

    def check_key_file(self, **kwargs):
        return check_key_file(
            key_path=self.resolve_key_path(),
            **kwargs
        )

    def check_vault(self, **kwargs):
        return check_vault(
            db_path=self.db_path,
            **kwargs
        )
    
    # ----------------------------
    # Core operations
    # ----------------------------

    def get(
        self, 
        service: str, 
        item: str, 
        fail: bool = False,
        crypto_backend=None
        ):
        backend = crypto_backend or self.crypto_backend
        
        self.ensure_vault_or_raise()

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT encrypted_secret FROM credentials WHERE service=? AND item=?",
                (service, item)
            ).fetchone()
        finally:
            conn.close()

        if not row:
            if fail:
                raise KeyError(f"Missing {service}/{item}")
            return None

        return backend.decrypt(row[0]).decode()

    def set(
        self,
        service: str,
        item: str,
        value: str,
        overwrite: bool = True,
        crypto_backend=None
    ):
        self.ensure_vault_or_raise()

        backend = crypto_backend or self.crypto_backend
        encrypted = backend.encrypt(value.encode())

        conn = sqlite3.connect(self.db_path)

        try:
            if overwrite:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO credentials
                    (service, item, encrypted_secret)
                    VALUES (?, ?, ?)
                    """,
                    (service, item, encrypted),
                )

            else:
                try:
                    conn.execute(
                        """
                        INSERT INTO credentials
                        (service, item, encrypted_secret)
                        VALUES (?, ?, ?)
                        """,
                        (service, item, encrypted),
                    )

                except sqlite3.IntegrityError:
                    raise KeyError(
                        f"Credential already exists: {service}/{item}"
                    )

            conn.commit()

        finally:
            conn.close()
            
    def remove(self, service: str, item: str) -> bool:
        self.ensure_vault_or_raise()

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "DELETE FROM credentials WHERE service=? AND item=?",
                (service, item),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def list_contents(self):
        self.ensure_vault_or_raise()

        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT service, item FROM credentials"
            ).fetchall()
        finally:
            conn.close()

    # --- Wrappers around vault functions ---
    # To pass the db_path attribute. Use **kwargs to relieve maintenance burden for wrappers.
    # An AI removed these wrappers - why?
    def export_vault(self,**kwargs):
        from .actions import export_vault
        return export_vault(self.db_path,**kwargs)
    def rotate_key(self,**kwargs):
        from .key import rotate_key
        return rotate_key(client=self,**kwargs)
    def backup_vault(self,**kwargs):
        from .actions import backup_vault
        return backup_vault(self.db_path,**kwargs)
    def import_records(self,json_path:str|Path,**kwargs):
        from .actions import import_records 
        # json_path keyword explcitly provided because the function is otherwise useless
        return import_records(client=self,json_path=json_path,**kwargs) 
