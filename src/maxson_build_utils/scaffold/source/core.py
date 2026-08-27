# src/maxson_build_utils/scaffold/source/core.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject


CORE_TEMPLATE = Template(
    """\
# src/$import_name/core.py

from __future__ import annotations
"""
)


def render_core_py(import_name: str) -> str:
    """Render the standard core module."""
    return CORE_TEMPLATE.substitute(
        import_name=import_name,
    )


def run_init_core(
    root_dir: Path | str | None = None,
) -> WriteResult:
    """Scaffold core.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.src_dir / "core.py"

    text = render_core_py(
        import_name=pyproject.import_name,
    )

    return write_str_to_file(
        target_path,
        text=text,
    )
