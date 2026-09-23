# src/dworshak_secret/errors.py
from __future__ import annotations


class MissingKeyError(FileNotFoundError):
    """
    Raised when a vault key cannot be located.

    This indicates a misconfiguration or missing initialization
    of the vault, not a cryptographic failure.
    """
    def __init__(self, message: str, key_path=None):
        super().__init__(message)
        self.key_path = key_path

class VaultError(Exception):
    """Base class for dworshak-secret errors."""
    pass

class WrongKeyError(VaultError):
    """Raised when secrets cannot be decrypted (bad key)."""
    pass