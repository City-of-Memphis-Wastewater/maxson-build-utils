# src/maxson_build_utils/context.py
from __future__ import annotations
from pathlib import Path

from .pyproject import PyProject
_pyproject = PyProject()

APP_NAME = _pyproject.app_name
APP_NAME_PRETTY = _pyproject.pretty_name
IMPORT_NAME = _pyproject.import_name
SRC_DIR = _pyproject.src_dir
SRC_FOLDER_NAME = IMPORT_NAME
APP_DIR = _pyproject.app_dir
LOG_FILE_PATH = _pyproject.log_file_path
SERVICE = APP_NAME
DESCRIPTION_STR = "Centralized build and packaging tools for the standard Maxson architecture."
