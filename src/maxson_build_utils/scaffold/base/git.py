# src/maxson_build_utils/scaffold/base/git.py

from __future__ import annotations

import subprocess
from pathlib import Path


def run_init_git(
    root_dir: Path | str | None = None,
) -> Path:
    """Initialize a Git repository."""
    root = Path(root_dir or ".").resolve()

    subprocess.run(
        ["git", "init"],
        cwd=root,
        check=True,
    )

    return root / ".git"
