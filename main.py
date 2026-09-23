# main.py
"""Root shim to satisfy Buildozer/p4a entry point requirements."""
from __future__ import annotations

import sys
from pathlib import Path

# Inject src directory into sys.path before importing internal packages
APP_DIR = Path(__file__).resolve().parent
SRC_DIR = APP_DIR / "src"

if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from maxson_build_utils.__buildozer_entry__ import main

if __name__ == "__main__":
    main()
