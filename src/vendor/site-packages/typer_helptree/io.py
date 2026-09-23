#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# src/typer_helptree/io.py
from __future__ import annotations
import json
import logging
import os
import sys
import datetime
from pathlib import Path
from typing import Dict, Any
import pyhabitat
from enum import Enum

# --- Configuration ---
try:
    HELPTREE_HOME = Path.home() / ".typer_helptree"
except Exception:
    HELPTREE_HOME = Path("/tmp/.typer_helptree_temp")

HELPTREE_HOME.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = HELPTREE_HOME / "helptree_errors.log"

# --- Logging Setup ---
def setup_error_logger():
    """Configures a logger for background error tracking."""
    logger = logging.getLogger('typer_helptree')
    logger.setLevel(logging.WARNING)
    logger.propagate = False

    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        fh = logging.FileHandler(LOG_FILE_PATH, mode='a')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    return logger

error_logger = setup_error_logger()

# --- JSON serialization safety ---

class UniversalEncoder(json.JSONEncoder):
    """
    A general-purpose JSON encoder that handles Enums, 
    objects with __str__ methods, and other non-serializable types.
    """
    def default(self, obj):
        # 1. Handle Enums (Return the raw value like 'console')
        if isinstance(obj, Enum):
            return obj.value
        
        # 2. Handle types/classes (Return the name like 'Choice' or 'Path')
        if isinstance(obj, type):
            return obj.__name__
            
        # 3. Fallback: If it can be a string, make it a string
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
        
# --- Export Functionality ---

def export_help_json(
        data: Dict[str, Any], 
        app_name: str, 
        version: str, 
        output_dir: str | Path | None = None
        ) -> Path:
    """Exports the CLI structure as a machine-readable JSON file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_json = f"{app_name}_v{version}_tree_{timestamp}.json"
    
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_path = output_dir / filename_json
    else:
        output_path = get_default_output_dir() / filename_json

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, cls=UniversalEncoder)
        print(f"JSON structure exported: {get_friendly_path(output_path)}", file=sys.stderr)
        return output_path
    except Exception as e:
        error_logger.error(f"JSON export failed: {e}", exc_info=True)
        raise RuntimeError(f"JSON export failed: {e}")

def export_help_txt(
        text_content: str, 
        app_name: str, 
        version: str, 
        output_dir: str | Path | None = None
        ) -> Path:
    """Exports the CLI structure as a plain text file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_txt = f"{app_name}_v{version}_tree_{timestamp}.txt"
    
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_path = output_dir / filename_txt
    else:
        output_path = get_default_output_dir() / filename_txt
        
    try:
        output_path.write_text(text_content, encoding='utf-8')
        print(f"TXT structure exported: {get_friendly_path(output_path)}", file=sys.stderr)
        return output_path
    except Exception as e:
        error_logger.error(f"TXT export failed: {e}", exc_info=True)
        raise RuntimeError(f"TXT export failed: {e}")

def export_help_svg(
        console, 
        app_name: str, 
        version:str, 
        output_dir: str | Path | None = None
        ) -> Path:
    """Exports the recorded console content as an SVG file."""

    filename_svg = f"{app_name}_v{version}_helptree.svg"
    
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_path = output_dir / filename_svg
    else:
        output_path = get_default_output_dir() / filename_svg

    try:
        # Rich's console must have record=True for this to work
        console.save_svg(str(output_path), title=f"{app_name} CLI Help Tree")
        print(f"SVG structure exported: {get_friendly_path(output_path)}", file=sys.stderr)
        return output_path
    except Exception as e:
        error_logger.error(f"SVG export failed: {e}", exc_info=True)
        raise RuntimeError(f"SVG export failed: {e}")

# --- Helpers --- 

def get_default_output_dir(use_assets: bool = False) -> Path:
    """Returns the target directory. Assets pathing not expected here, use output_dir arg."""
    dest = HELPTREE_HOME
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def get_friendly_path(full_path: Path) -> str:
    """Returns absolute path on Windows or tilde-shortened path on Unix."""
    if pyhabitat.on_windows():
        return str(full_path.resolve())
    
    try:
        home = Path.home()
        if full_path.is_relative_to(home):
            return f"~{os.sep}{full_path.relative_to(home)}"
    except Exception:
        export_help_json(data, app_name, version, export_path)
    return str(full_path)

def get_export_path()-> Path:
    return HELPTREE_HOME

