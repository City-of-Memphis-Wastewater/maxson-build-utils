# src/dworshak_secret/crypto/base.py
from __future__ import annotations
from typing import Protocol


class CryptoBackend(Protocol):
    """
    Contract for encryption backends used by DworshakSecret.

    Any implementation must provide:
    - encrypt(bytes) -> bytes
    - decrypt(bytes) -> bytes
    """

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt plaintext bytes and return ciphertext bytes.
        """
        ...

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt ciphertext bytes and return plaintext bytes.
        """
        ...
