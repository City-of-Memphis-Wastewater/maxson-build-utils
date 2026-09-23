# src/maxson_build_utils/__buildozer_entry__.py
"""Buildozer / Android runtime orchestration entry point."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .vendor import VENDOR_SITE_PACKAGES_DIR

def bootstrap_environment() -> None:
    """Configure paths and environment variables before Kivy initializes."""
    # Root main.py is 2 levels up from src/maxson_build_utils/
    base_dir = Path(__file__).resolve().parent.parent.parent
    src_dir = base_dir / "src"
    vendor_dir = VENDOR_SITE_PACKAGES_DIR

    os.environ.setdefault("KIVY_HOME", str(base_dir / ".kivy"))
    os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

    for directory in (base_dir, src_dir, vendor_dir):
        if directory.exists():
            dir_str = str(directory)
            if dir_str not in sys.path:
                sys.path.insert(0, dir_str)


def main() -> None:
    """Orchestrates application startup for Buildozer."""
    bootstrap_environment()

    from maxson_build_utils.kivy.app import launch_kivy_app

    launch_kivy_app()


if __name__ == "__main__":
    main()
