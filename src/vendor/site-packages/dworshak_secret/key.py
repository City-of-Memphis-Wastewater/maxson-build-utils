# src/dworshak_secret/key.py
"""
Helper module focused on Fernet key operations:
- loading the current key
- generating new keys
- orchestrating key rotation (with dry-run support)

"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Tuple, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
import sys

if TYPE_CHECKING:
    from .core import DworshakSecret

from .paths import resolve_key_path_for_db, ensure_secure_permissions
from .registry import register_vault_key

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet=None
    InvalidToken=None
    MultiFernet=None
    
from .paths import KEY_FILE, DB_FILE

#@dataclass
#class VaultKey:
#    key: bytes
#    key_path: Path | None = None

class VaultKey:
    def __init__(self, key_bytes: bytes, path: Path):
        self._key = key_bytes
        self.path = path

    def get_bytes(self):
        return self._key

    def __repr__(self):
        return "VaultKey(key=<redacted>)"
    def __str__(self):
        return self.__repr__()
        
MSG_CRYPTO_HELP = (
    "Encryption is not available. Install with crypto extra:\n"
    "  uv add \"dworshak-secret[crypto]\"\n"
    "  or\n"
    "  pip install \"dworshak-secret[crypto]\"\n"
    "On Termux, use \"pkg add python-cryptography\"\n"
    "On iSH alpine, use \"apk add py3-cryptography\"\n"
    "For Termux and iSH, ensure that you include --system-site-packages."
)

def check_key_path(key_path: Path | str) -> Path:
    key_path = Path(key_path).absolute()
    if not key_path.exists():
        raise FileNotFoundError(f"Encryption key file not found at {key_path}")
    return key_path

def load_current_key(
    db_path: Path | str | None = None,
    key_path: Path | str | None = None
) -> bytes:
    target_key_path = resolve_key_path_for_db(db_path, key_path)
    check_key_path(target_key_path)
    return target_key_path.read_bytes()

def generate_new_key() -> bytes:
    """Generate a fresh Fernet-compatible key (32 bytes base64-encoded)."""
    installation_check()
    return Fernet.generate_key()


def create_vault_key(db_path, key_path):
    installation_check()
    if Path(key_path).exists():
        raise FileExistsError(f"Key file already exists: {key_path}")
    key_path.parent.mkdir(parents=True, exist_ok=True)

    key = Fernet.generate_key()
    key_path.write_bytes(key)
    ensure_secure_permissions(key_path)

    register_vault_key(db_path, {
        "key_path": str(Path(key_path).resolve()),
    })

    return VaultKey(key,key_path)

def rotate_key(
    client: DworshakSecret,
    dry_run: bool = False,
    auto_backup: bool = True,
    extra_backup_suffix: str = "pre-key-rotation",
) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Perform (or simulate) a full key rotation.

    Steps:
    1. Check vault health
    2. (Optional) Create backup
    3. Generate new key
    4. Use MultiFernet to decrypt with old key, encrypt with new
    5. Re-write every credential (only if not dry_run)
    6. Replace key file on disk (only if not dry_run)

    Returns:
        (success: bool, message: str, affected_credentials: list[str] | None)
    """
    from .actions import backup_vault
    from .vault import check_vault 
    from .paths import ensure_secure_permissions
    from .crypto.fernet import FernetBackend
    #from cryptography.fernet import Fernet
    
    installation_check()
    key_path = client.resolve_key_path()
    
    vault_status = client.check_vault()
    key_status = client.check_key_file()
    if not vault_status.is_valid:
        return False, f"Vault is unhealthy: {vault_status.message}", None

    # ── Backup phase ──
    backup_path: Optional[Path] = None
    if auto_backup:
        backup_path = backup_vault(
            extra_suffix=extra_backup_suffix,
            include_timestamp=True,
        )
        if backup_path is None:
            return False, "Automatic backup failed — rotation aborted", None

    backup_info = f"Backup created at {backup_path}" if backup_path else "No backup performed"

    # ── Prepare keys ──
    try:
        old_key = load_current_key(client.db_path, key_path)
    except FileNotFoundError as exc:
        return False, f"Cannot rotate: {exc}", None

    new_key = generate_new_key()

    # MultiFernet allows decrypting with old key while encrypting with new
    transition_fernet = MultiFernet([Fernet(new_key), Fernet(old_key)])
    
    transition_backend = FernetBackend.from_fernet(
        transition_fernet
    )

    # ── Re-encryption phase ──
    credentials = client.list_contents()
    if not credentials:
        return True, f"No credentials to rotate. {backup_info}", []

    affected: List[str] = []
    conn = None

    try:
        conn = sqlite3.connect(client.db_path)
        conn.row_factory = sqlite3.Row
        
        for service, item in credentials:
            plaintext = client.get(
                            service, 
                            item
                            )
            if plaintext is None:
                return False, f"Failed to read secret {service}/{item}", affected

            affected.append(f"{service}/{item}")

            if dry_run:
                continue

            # Re-store using transition fernet (encrypts with primary = new key)
            client.set(
                        service = service, 
                        item = item, 
                        value = plaintext, 
                        crypto_backend=transition_backend
                        )
        if dry_run:
            return (
                True,
                f"Dry run. A true key rotation would re-encrypt {len(affected)} credential(s). {backup_info}",
                affected,
            )

        conn.commit()

        # Atomically replace the key file
        key_path.write_bytes(new_key)
        ensure_secure_permissions(key_path)

        return (
            True,
            f"Successfully rotated key and re-encrypted {len(affected)} credential(s). {backup_info}",
            affected,
        )

    except InvalidToken as exc:
        return False, f"Decryption failure during rotation: {exc}", affected
    except Exception as exc:
        if conn:
            conn.rollback()
        return False, f"Rotation failed: {exc}", affected
    finally:
        if conn:
            conn.close()

def rotate_key_dry_run(client: DworshakSecret) -> Tuple[bool, str, Optional[List[str]]]:
    """
    Convenience wrapper — always runs in dry-run mode.
    Checks the key relative to a db path.
    """
    return rotate_key(client=client, dry_run=True, auto_backup=False)

def installation_check(die = True):
    if not CRYPTO_AVAILABLE:
        print(MSG_CRYPTO_HELP, file=sys.stderr)
        if die:
            sys.exit(1)
        return False
    return True
'''
def rotate_vault_key(db_path: Path, old_key_bytes: bytes, new_key_bytes: bytes):
    """Decrypts the entire vault database with the old key and re-encrypts with the new key."""
    
    # 1. Read and decrypt everything using old bytes
    raw_decrypted_payload = decrypt_entire_database(db_path, old_key_bytes)
    
    # 2. Re-encrypt using new bytes
    new_encrypted_payload = encrypt_entire_database(raw_decrypted_payload, new_key_bytes)
    
    # 3. Atomic write back to the database path
    tmp_db = db_path.with_suffix(".tmp")
    tmp_db.write_bytes(new_encrypted_payload)
    tmp_db.replace(db_path)
    
    # 4. Update your fingerprint registry with the new signature
    new_fingerprint = calculate_key_fingerprint(new_key_bytes)
    update_registry_fingerprint(db_path, new_fingerprint)
'''
if __name__ == "__main__":
    installation_check()
