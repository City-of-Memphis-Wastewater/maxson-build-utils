# src/maxson_build_utils/scaffold/source/kivy.py
from __future__ import annotations

from pathlib import Path

from ...helpers import WriteResult, write_str_to_file
from ...pyproject import MaxsonPyProject

MAIN_KV_TEMPLATE = """\
# Main Kivy UI layout file
<RootWidget>:
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: 'Welcome to {APP_NAME}'
"""

APP_PY_TEMPLATE = """\
# src/{IMPORT_NAME}/kivy/app.py
from __future__ import annotations

from kivy.app import App
from kivy.uix.label import Label


class {CLASS_NAME}App(App):
    def build(self):
        return Label(text="Hello from {APP_NAME}!")


def launch_kivy_app() -> None:
    app = {CLASS_NAME}App()
    app.run()
"""

BUILDOZER_ENTRY_TEMPLATE = """\
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


def run_init_kivy(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    """Scaffold Kivy module and __buildozer_entry__.py."""
    target_dir = Path(root_dir) if root_dir else Path.cwd()
    pyproject = MaxsonPyProject(target_dir / "pyproject.toml")

    import_name = pyproject.import_name
    app_name = pyproject.app_name
    class_name = _to_pascal_case(import_name)

    pkg_dir = target_dir / "src" / import_name
    kivy_dir = pkg_dir / "kivy"
    kivy_dir.mkdir(parents=True, exist_ok=True)

    results: list[WriteResult] = []

    # 1. Write src/<import_name>/kivy/__init__.py
    results.append(
        write_str_to_file(
            path=kivy_dir / "__init__.py",
            text="",
        )
    )

    # 2. Write src/<import_name>/kivy/main.kv
    results.append(
        write_str_to_file(
            path=kivy_dir / "main.kv",
            text=MAIN_KV_TEMPLATE.format(APP_NAME=app_name),
        )
    )

    # 3. Write src/<import_name>/kivy/app.py
    results.append(
        write_str_to_file(
            path=kivy_dir / "app.py",
            text=APP_PY_TEMPLATE.format(
                IMPORT_NAME=import_name,
                APP_NAME=app_name,
                CLASS_NAME=class_name,
            ),
        )
    )
    """
    # wrong, belongs in run_init_buildozer
    # 4. Write src/<import_name>/__buildozer_entry__.py
    results.append(
        write_str_to_file(
            path=pkg_dir / "__buildozer_entry__.py",
            text=BUILDOZER_ENTRY_TEMPLATE.format(IMPORT_NAME=import_name),
        )
    )
    """
    return results
