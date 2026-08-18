# src/maxson_build_utils/scaffold/_main.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject

# ---------------------------------------------------------------------------
# Template Definition
# ---------------------------------------------------------------------------

MAIN_TEMPLATE = Template(
    """\
# src/$import_name/__main__.py
from __future__ import annotations

from $import_name.cli import app

if __name__ == "__main__":
    app()
"""
)


# ---------------------------------------------------------------------------
# Rendering & Entry Point
# ---------------------------------------------------------------------------

def render_main_py(import_name: str) -> str:
    """Render the standard forwarded __main__.py content."""
    return MAIN_TEMPLATE.substitute(import_name=import_name)


def run_init_main(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Scaffold __main__.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.src_dir / "__main__.py"

    text = render_main_py(import_name=pyproject.import_name)

    return write_str_to_file(target_path, text=text, overwrite=overwrite)
