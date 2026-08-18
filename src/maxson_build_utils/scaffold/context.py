# src/maxson_build_utils/scaffold/context.py
from __future__ import annotations
from pathlib import Path
from string import Template
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file

CONTEXT_TEMPLATE = Template(
    """\
# src/$import_name/context.py
from __future__ import annotations

from maxson_build_utils.pyproject import PyProject

_pyproject = PyProject()

APP_NAME = _pyproject.app_name
APP_NAME_PRETTY = _pyproject.pretty_name
IMPORT_NAME = _pyproject.import_name
SRC_DIR = _pyproject.src_dir
SRC_FOLDER_NAME = IMPORT_NAME

SERVICE = APP_NAME
DESCRIPTION_STR = _pyproject.get("project", "description")

APP_DIR = _pyproject.app_dir
LOG_FILE_PATH = _pyproject.log_file_path
"""
)


def render_context_py(import_name: str) -> str:
    return CONTEXT_TEMPLATE.substitute(import_name=import_name)


def run_init_context(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    pyproject = PyProject(root_dir)

    target_path = pyproject.src_dir / "context.py"

    text = render_context_py(
        import_name=pyproject.import_name,
    )

    return write_str_to_file(
        target_path,
        text=text,
        overwrite=overwrite,
    )
