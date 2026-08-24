# src/maxson_build_utils/scaffold/context.py
from __future__ import annotations
from pathlib import Path
from string import Template
import logging
logger = logging.getLogger(__name__)

from ..helpers import write_str_to_file, WriteResult
from ..pyproject import MaxsonPyProject

CONTEXT_TEMPLATE = Template(
    """\
# src/$import_name/context.py
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from maxson_build_utils.pyproject import MaxsonPyProject
from maxson_build_utils.names import to_title_case, to_kebab_case, to_snake_case

PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent


@lru_cache(maxsize=1)
def get_pyproject() -> MaxsonPyProject:
    proj = MaxsonPyProject(PROJECT_ROOT)
    if proj.path is None:
        proj = MaxsonPyProject(Path.cwd())
    return proj


def get_app_name() -> str:
    proj = get_pyproject()
    if proj.app_name:
        return proj.app_name
    return to_kebab_case(PACKAGE_DIR.name)


def get_pretty_name() -> str:
    proj = get_pyproject()
    if proj.pretty_name:
        return proj.pretty_name
    return to_title_case(PACKAGE_DIR.name)


def get_import_name() -> str:
    proj = get_pyproject()
    if proj.import_name:
        return proj.import_name
    return to_snake_case(PACKAGE_DIR.name)


def get_description() -> str:
    desc = get_pyproject().get("project", "description")
    if desc:
        return desc
    return get_pretty_name()


def get_app_dir() -> Path:
    proj = get_pyproject()
    if proj.app_dir is not None:
        return proj.app_dir
    path = Path.home() / f".{get_app_name()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_file_path() -> Path:
    proj = get_pyproject()
    if proj.log_file_path is not None:
        return proj.log_file_path
    cache_dir = Path.home() / ".cache" / get_app_name()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{get_app_name()}_errors.log"


APP_NAME = get_app_name()
APP_NAME_PRETTY = get_pretty_name()
IMPORT_NAME = get_import_name()
SRC_FOLDER_NAME = IMPORT_NAME
DESCRIPTION_STR = get_description()
APP_DIR = get_app_dir()
LOG_FILE_PATH = get_log_file_path()
SERVICE = APP_NAME
"""
)


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
