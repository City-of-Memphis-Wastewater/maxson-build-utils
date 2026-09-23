# pyhabitat/_compat.py
from __future__ import annotations
import sys
from functools import lru_cache, wraps

if sys.version_info >= (3, 9):
    from functools import cache
else:
    # Backport functools.cache for Python < 3.9
    def cache(func):
        """Mimic functools.cache using lru_cache(maxsize=None)."""
        cached_func = lru_cache(maxsize=None)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return cached_func(*args, **kwargs)

        # Optional: allow clearing cache like functools.cache
        wrapper.cache_clear = cached_func.cache_clear
        return wrapper
