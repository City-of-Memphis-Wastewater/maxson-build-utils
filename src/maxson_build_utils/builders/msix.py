#!/usr/bin/env python3
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
import xml.etree.ElementTree as ET

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
    onedir_path: Path = Path("dist/onedir"),
    manifest_path: Path = Path("packaging/msix/AppxManifest.xml"),
    output_dir: Path = Path("dist/msix"),
    output_name: str | None = None,
) -> Path:
    if sys.platform != "win32":
        raise RuntimeError(
            "Local MSIX builds require Windows and the Windows SDK. "
            "Use the GitHub MSIX workflow to build the package on Windows."
        )

    makeappx_path = find_makeappx()

    if not onedir_path.is_dir():
        raise FileNotFoundError(f"PyInstaller OneDir payload not found at '{onedir_path}'")

    if not manifest_path.is_file():
        raise FileNotFoundError(f"MSIX manifest not found at '{manifest_path}'")

    # Validate manifest and retrieve target executable name
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    
    # Handle XML namespaces commonly present in AppxManifest.xml
    namespaces = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
    ns_prefix = 'ns:' if namespaces else ''

    app_node = root.find(f".//{ns_prefix}Application", namespaces)
    if app_node is None or "Executable" not in app_node.attrib:
        raise ValueError("MSIX manifest missing <Application Executable='...'> attribute.")

    exe_name = app_node.attrib["Executable"]
    exe_target = onedir_path / exe_name

    if not exe_target.is_file():
        raise FileNotFoundError(
            f"Manifest expects executable '{exe_name}', but it was not found in '{onedir_path}'."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_name:
        output_name = f"{Path.cwd().name}.msix"

    final_output_path = output_dir / output_name

    # Stage files and invoke MakeAppx
    with tempfile.TemporaryDirectory() as temp_dir:
        stage_dir = Path(temp_dir) / "msix_stage"
        
        # 1. Copy OneDir payload
        shutil.copytree(onedir_path, stage_dir)

        # 2. Copy AppxManifest.xml
        shutil.copy2(manifest_path, stage_dir / "AppxManifest.xml")

        # 3. Copy Assets directory if present alongside manifest
        assets_dir = manifest_path.parent / "Assets"
        if assets_dir.is_dir():
            shutil.copytree(assets_dir, stage_dir / "Assets", dirs_exist_ok=True)

        # 4. Run MakeAppx pack command
        cmd = [
            str(makeappx_path),
            "pack",
            "/v",
            "/h", "SHA256",
            "/d", str(stage_dir),
            "/p", str(final_output_path.resolve()),
            "/o",  # Overwrite existing output if present
        ]

        logger.info("Executing MakeAppx command: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error("MakeAppx stdout: %s", result.stdout)
            logger.error("MakeAppx stderr: %s", result.stderr)
            raise RuntimeError(f"MakeAppx.exe failed with exit code {result.returncode}")

    logger.info("Successfully created MSIX package at: %s", final_output_path)
    return final_output_path
