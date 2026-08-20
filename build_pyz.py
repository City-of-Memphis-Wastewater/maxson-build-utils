#!/usr/bin/env python3
# ./build_pyz.py
"""
Builds the portable Python ZipApp (PYZ) using maxson_build_utils.
"""

from __future__ import annotations

from maxson_build_utils._version import __version__
from maxson_build_utils.context import IMPORT_NAME
from maxson_build_utils.build_pyz import run_build_pyz

if __name__ == "__main__":
    run_build_pyz(
        src_folder_name=IMPORT_NAME,
        version=__version__,
        entry_point="maxson_build_utils.__main__:app",
        test_gui=False
    )
