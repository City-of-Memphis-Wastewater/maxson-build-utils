# src/maxson_build_utils/scaffold/config.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ..helpers import write_str_to_file, WriteResult
from ..pyproject import MaxsonPyProject


CONFIG_TEMPLATE = Template(
    """\
# src/$import_name/config.py
from __future__ import annotations


def get_config_mngr():
    from .context import APP_DIR
    from dworshak_config import DworshakConfig
    return DworshakConfig(path=APP_DIR / "config.json")

"""
)


def render_config_py(import_name: str) -> str:
    """Render the standard application configuration helper."""
    return CONFIG_TEMPLATE.substitute(
        import_name=import_name,
    )


def run_init_config(
    root_dir: Path | str | None = None,
) -> WriteResult:
    """Scaffold config.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.src_dir / "config.py"

    text = render_config_py(
        import_name=pyproject.import_name,
    )

    return write_str_to_file(
        target_path,
        text=text,
    )
