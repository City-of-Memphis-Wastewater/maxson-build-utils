# src/dworshak_secret/fingerprint.py

import hashlib

def calculate_key_fingerprint(key_bytes: bytes) -> str:
    """Generate a non-reversible unique signature of the key."""
    return hashlib.sha256(key_bytes).hexdigest()
