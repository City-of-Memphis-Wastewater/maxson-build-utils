# src/maxson_build_utils/scaffold/source/config.py

from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject
from ...rendering import render_template


CONFIG_TEMPLATE = """\
# src/@@import_name@@/config.py
from __future__ import annotations


def get_config_mngr():
    from .context import APP_DIR
    from dworshak_config import DworshakConfig
    return DworshakConfig(path=APP_DIR / "config.json")
"""


def run_init_config(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Scaffold config.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.package_dir / "config.py"

    text = render_template(
        template_str=CONFIG_TEMPLATE,
        context={
            "import_name": pyproject.import_name,
        },
    )

    return write_str_to_file(
        path=target_path,
        text=text,
        overwrite=overwrite,
    )
