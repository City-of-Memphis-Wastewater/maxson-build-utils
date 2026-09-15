#!/usr/bin/env python3
# src/maxson_build_utils/builders/msix.py

"""Build utilities for packaging PyInstaller outputs to the Microsoft Store."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import pyhabitat

from ..helpers import PyinsMode, IconFileType, resolve_icon_filetype, resolve_icon_path
from ..state import get_pyinstaller_onedir_export_entrypoint_path

logger = logging.getLogger(__name__)
def find_makeappx() -> Path:
    candidates = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin").glob(
            r"*\x64\makeappx.exe"
        ),
        Path(r"C:\Program Files\Windows Kits\10\bin").glob(
            r"*\x64\makeappx.exe"
        ),
    ]

    matches = sorted(
        (path for group in candidates for path in group),
        reverse=True,
    )

    if not matches:
        raise RuntimeError(
            "MakeAppx.exe was not found. "
            "Install the Windows 10/11 SDK."
        )

    return matches[0]


def build_msix(
    exe_path: Path | None = None,
    output_dir: Path = Path("dist/msix"),
) -> Path:
    if sys.platform != "win32":
        raise RuntimeError(
            "Local MSIX builds require Windows and the Windows SDK. "
            "Use the GitHub MSIX workflow to build the package on Windows."
        )
    pass
