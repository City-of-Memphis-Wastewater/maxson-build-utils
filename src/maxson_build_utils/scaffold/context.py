# src/maxson_build_utils/scaffold/context.py
from __future__ import annotations
from pathlib import Path
#from string import Template
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file, WriteResult
from ..pyproject import MaxsonPyProject
from ..rendering import get_template_context, render_template

CONTEXT_TEMPLATE = """\
# src/@@import_name@@/context.py
from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

APP_NAME = @@app_name@@
APP_NAME_PRETTY = @@pretty_name@@
IMPORT_NAME = @@import_name@@
SRC_FOLDER_NAME = @@import_name@@
DESCRIPTION_STR = @@description@@
APP_DIR = Path.home() / ".@@app_name@@"
LOG_FILE_PATH = @@log_path@@
SERVICE = APP_NAME
"""

'''
def render_context_py(import_name: str) -> str:
    return CONTEXT_TEMPLATE.substitute(import_name=import_name)


def run_init_context(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    pyproject = MaxsonPyProject(root_dir)

    src_dir = pyproject.src_dir
    if src_dir is None:
        root = Path(root_dir) if root_dir else Path.cwd()
        import_name = pyproject.import_name or root.name.replace("-", "_")
        src_dir = root / "src" / import_name

    target_path = src_dir / "context.py"

    text = render_context_py(
        import_name=pyproject.import_name or src_dir.name,
    )

    return write_str_to_file(
        target_path,
        text=text,
        overwrite=overwrite,
    )
'''
def run_init_context(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    pyproject = MaxsonPyProject(root_dir)

    context = get_template_context(pyproject)

    text = render_template(
        text=CONTEXT_TEMPLATE,
        context=context,
    )

    return write_str_to_file(
        target_path = pyproject.src_dir / "context.py",
        text=text,
        overwrite=overwrite,
    )
