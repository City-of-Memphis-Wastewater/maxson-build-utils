# src/dworshak_secret/crytpo/fernet.py
from __future__ import annotations
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from .base import CryptoBackend
from ..security import get_fernet
from ..errors import WrongKeyError

class FernetBackend(CryptoBackend):
    def __init__(self, key_str):
        self.fernet = get_fernet(key_str=key_str)
        
        if not self.fernet:
            raise RuntimeError("Crypto unavailable")

    @classmethod
    def from_fernet(cls, fernet_obj):
        obj = cls.__new__(cls)
        obj.fernet = fernet_obj
        return obj
                
    def encrypt(self, data: bytes) -> bytes:
        try:
            return self.fernet.encrypt(data)
        except InvalidToken:
            raise WrongKeyError("Invalid encryption key or corrupted data.") from None

    
    def decrypt(self, data: bytes) -> bytes:
        try:
            return self.fernet.decrypt(data)
        except InvalidToken:
            raise WrongKeyError("Invalid encryption key or corrupted data.") from None
