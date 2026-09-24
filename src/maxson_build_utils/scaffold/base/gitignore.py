# src/maxson_build_utils/scaffold/base/gitignore.py
"""
Use my custom .gitignore standard file.
"""

from __future__ import annotations

from pathlib import Path

from ...helpers import write_str_to_file,WriteResult


GITIGNORE = """\
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info/
vendor/

# Virtual environments
.venv/
.python-version

# local persistence
.persist

"""


def run_init_gitignore(
    root_dir: Path | str | None = None,
    overwrite: bool = False,
) -> WriteResult:
    """Create the standard Maxson .gitignore."""
    if not overwrite:
        return 
    root = Path(root_dir or ".").resolve()

    path = write_str_to_file(
        path = root / ".gitignore",
        text=GITIGNORE,
        overwrite=overwrite,
    )
    return path
