# src/maxson_build_utils/scaffold/git.py

from __future__ import annotations

import subprocess
from pathlib import Path


def run_init_git(
    root_dir: Path | str | None = None,
) -> None:
    """Initialize a Git repository."""
    root = Path(root_dir or ".").resolve()

    subprocess.run(
        ["git", "init"],
        cwd=root,
        check=True,
    )

