# src/maxson_build_utils/scaffold/gitignore.py
"""
Use my custom .gitignore standard file.
"""

from __future__ import annotations

from pathlib import Path

from ..helpers import write_str_to_file


GITIGNORE = """\
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info/

# Virtual environments
.venv/
.python-version
"""


def run_init_gitignore(
    root_dir: Path | str | None = None,
) -> Path:
    """Create the standard Maxson .gitignore."""
    root = Path(root_dir or ".").resolve()

    return write_str_to_file(
        root / ".gitignore",
        text=GITIGNORE,
    )
    
def run_init_gitignore():
    pass
