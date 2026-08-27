# src/maxson_build_utils/scaffold/source/helpers.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject


HELPERS_TEMPLATE = Template(
    """\
# src/$import_name/helpers.py

from __future__ import annotations
"""
)


def render_helpers_py(import_name: str) -> str:
    """Render the standard helpers module."""
    return HELPERS_TEMPLATE.substitute(
        import_name=import_name,
    )


def run_init_helpers(
    root_dir: Path | str | None = None,
) -> WriteResult:
    """Scaffold helpers.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.src_dir / "helpers.py"

    text = render_helpers_py(
        import_name=pyproject.import_name,
    )

    return write_str_to_file(
        target_path,
        text=text,
    )
