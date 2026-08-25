# src/maxson_build_utils/scaffold/__init__.py
from __future__ import annotations

# --- ci ---
from .github_workflows import run_init_github_workflows

__all__ = [
    # --- ci ---,
    "run_init_github_workflows",
]
