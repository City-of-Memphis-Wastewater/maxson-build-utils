# src/maxson_build_utils/scaffold/icons.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject
from ..icons import copy_stock_icons, bundled_icons

"""
"""

def run_init_icons(
    dst:Path|str|None=None,
    root_dir: Path | str | None = None
    ) -> Path:
    # We need a way to encourage used to add refs to their tools.maxson-build-utils.icons section, but we do not do a magi write
    
    if dst is None:
        pyproject = MaxsonPyProject(root_dir)
        dst = pyproject.icons_dir

    dst = Path(dst)

    if dst.resolve() == Path(bundled_icons()).resolve():
        logger.debug("Stock icon destination is the bundled icon directory; nothing to copy.")
        return dst

    return copy_stock_icons(dst)
