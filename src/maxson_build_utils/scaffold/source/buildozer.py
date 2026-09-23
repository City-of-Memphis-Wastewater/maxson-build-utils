# src/maxson_build_utils/scaffold/source/buildozer.py
# should place main.py shim in root and src/*/__buildozer_entry__.py pointing to either kivy app interface or somewhere else, like for webview. 

from __future__ import annotations

from pathlib import Path

from ...helpers import WriteResult, write_str_to_file
from ...context import PROJECT_ROOT, IMPORT_NAME, PACKAGE_DIR

ROOT_MAIN_PY_TEMPLATE = """\
# main.py
\"\"\"Root shim to satisfy Buildozer/p4a entry point requirements.\"\"\"
from __future__ import annotations

from {IMPORT_NAME}.__buildozer_entry__ import main

if __name__ == "__main__":
    main()
"""

BUILDOZER_ENTRY_KIVY_TEMPLATE = """\
# src/{IMPORT_NAME}/__buildozer_entry__.py
\"\"\"Buildozer / Android runtime orchestration entry point.\"\"\"
from __future__ import annotations

import os
import sys
from pathlib import Path


def bootstrap_environment() -> None:
    \"\"\"Configure paths and environment variables before Kivy initializes.\"\"\"
    # Root main.py is 2 levels up from src/{IMPORT_NAME}/
    base_dir = Path(__file__).resolve().parent.parent.parent
    src_dir = base_dir / "src"
    vendor_dir = base_dir / "vendor_for_buildozer"

    os.environ.setdefault("KIVY_HOME", str(base_dir / ".kivy"))
    os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

    for directory in (base_dir, src_dir, vendor_dir):
        if directory.exists():
            dir_str = str(directory)
            if dir_str not in sys.path:
                sys.path.insert(0, dir_str)


def main() -> None:
    \"\"\"Orchestrates application startup for Buildozer.\"\"\"
    bootstrap_environment()

    from {IMPORT_NAME}.kivy.app import launch_kivy_app

    launch_kivy_app()


if __name__ == "__main__":
    main()
"""


def _to_pascal_case(name: str) -> str:
    cleaned = name.replace("-", "_")
    return "".join(word.capitalize() for word in cleaned.split("_") if word)


def run_init_buildozer_source_entry(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    """Scaffold Kivy module and __buildozer_entry__.py."""

    results: list[WriteResult] = []

    # Write src/<import_name>/__buildozer_entry__.py
    results.append(
        write_str_to_file(
            path=PACKAGE_DIR / "__buildozer_entry__.py",
            text=BUILDOZER_ENTRY_KIVY_TEMPLATE.format(IMPORT_NAME=import_name),
        )
    )

    # Write main.py
    results.append(
        write_str_to_file(
            path=PROJECT_ROOT / "main.py",
            text=ROOT_MAIN_PY_TEMPLATE.format(IMPORT_NAME=import_name),
        )
    )

    return results
