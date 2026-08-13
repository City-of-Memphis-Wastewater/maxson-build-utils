# src/maxson_build_utils/scaffold/src.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ..pyproject import PyProject

"""
Ensure that the src/ dir is established in a project.
Expected to be run directly after `uv init`
"""

def run_init_src(root_dir:Path|None=None)->Path:
    """intended to be run after uv init"""
    pyproject = PyProject(root_dir)
    src_dir = pyproject.src_dir
    src_dir.mkdir(parents=True, exist_ok=True)
    return src_dir
