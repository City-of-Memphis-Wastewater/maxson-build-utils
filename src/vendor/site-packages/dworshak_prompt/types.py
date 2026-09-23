# src/dworshak_prompt/types.py
from __future__ import annotations
class SensitiveStr(str):
    """A string that masks its value in repr() calls."""
    def __repr__(self) -> str:
        return "'********'"