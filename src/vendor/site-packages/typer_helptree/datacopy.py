#!/usr/bin/env python3 
# SPDX-License-Identifier: MIT
# src/typer_helptree/datacopy.py
from __future__ import annotations
import shutil
import sys
from pathlib import Path
import importlib.resources as resources
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

APP_DIR = "typer_helptree"

# --- COPY LICENSE FILE TO PACKAGE DATA ---
def ensure_package_license(source_root_path: Path, package_data_path: Path):
    """Copies the root LICENSE file into the expected package data path."""
    source = source_root_path / "LICENSE"
    destination = package_data_path / "src" / APP_DIR / "data" / "LICENSE"

    if not source.exists():
        logger.warning(f"FATAL: Root license file not found at {source}!")
        sys.exit(1)

    logger.debug(f"Ensuring package license is copied to: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True) # Ensure data dir exists
    shutil.copy2(source, destination) # copy2 preserves metadata

# --- COPY README FILE TO PACKAGE DATA ---
def ensure_package_readme(source_root_path: Path, package_data_path: Path):
    """Copies the root README.md file into the expected package data path."""
    source = source_root_path / "README.md"
    destination = package_data_path / "src" / APP_DIR / "data" / "README.md"

    if not source.exists():
        logger.warning(f"FATAL: Root README file not found at {source}!")
        sys.exit(1)

    logger.debug(f"Ensuring package README is copied to: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True) # Ensure data dir exists
    shutil.copy2(source, destination) # copy2 preserves metadata


def ensure_data_files_for_build():
    logger.debug(f"PROJECT_ROOT = {PROJECT_ROOT}")
    ensure_package_license(PROJECT_ROOT, PROJECT_ROOT)
    ensure_package_readme(PROJECT_ROOT, PROJECT_ROOT)

def get_data_root() -> Path:
    """
    Returns the path to the 'data' directory bundled with package.
    Works for both source code and installed package.
    """
    try:
        # Python ≥3.9: use importlib.resources.files
        return resources.files(APP_DIR) / "data"
    except Exception:
        # Fallback: assume running from source
        return Path(__file__).resolve().parent / "data"

if __name__ == "__main__":
    ensure_data_files_for_build()
