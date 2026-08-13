# src/maxson_build_utils/scaffold/changelog.py
from __future__ import annotations
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from .helpers import write_str_to_file
from .pyproject import PyProject


def run_init_changelog()->Path:
    """Write blank changelog file to docs/CHANGELOG.md"""
    changelog = Path.cwd() / "docs" / "CHANGELOG.md"
    new_changelog="""
# Changelog

All notable changes to this project will be documented in this file.
The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.0] - YYYY-MM-DD
### Added:
-

---
"""
    write_str_to_file(path=changelog,text=new_changelog)
    return changelog
