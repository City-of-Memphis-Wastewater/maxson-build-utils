# src/maxson_build_utils/scaffold/source/context.py
from __future__ import annotations
from pathlib import Path
#from string import Template
import logging
logger = logging.getLogger(__name__)

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject
from ...rendering import get_template_context, render_template

CONTEXT_TEMPLATE = """\
# src/@@import_name@@/context.py
from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

APP_NAME = "@@app_name@@"
APP_NAME_PRETTY = "@@pretty_name@@"
IMPORT_NAME = "@@import_name@@"
SRC_FOLDER_NAME = "@@import_name@@"
DESCRIPTION_STR = "@@description@@"
APP_DIR = Path.home() / ".@@app_name@@"
LOG_FILE_PATH = APP_DIR / "@@app_name@@.log"
SERVICE = APP_NAME
CONFIG_PATH = APP_DIR / "config.json"
SECRET_PATH = APP_DIR / "vault.db"
ENV_PATH = PROJECT_ROOT / ".env"
"""

def run_init_context(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    pyproject = MaxsonPyProject(root_dir)

    context = get_template_context(pyproject)
    text = render_template(
        template_str=CONTEXT_TEMPLATE,
        context=context,
    )

    return write_str_to_file(
        path = pyproject.src_dir / "context.py",
        text=text,
        overwrite=overwrite,
    )
