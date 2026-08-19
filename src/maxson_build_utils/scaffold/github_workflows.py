# src/maxson_build_utils/scaffold/github_workflows.py

from __future__ import annotations
from pathlib import Path


def run_init_github_workflows(
    root_dir: Path | str | None = None,
) -> Path:
    """Create the GitHub Actions workflows directory."""
    root = Path(root_dir or ".").resolve()
    workflows_dir = root / ".github" / "workflows"

    workflows_dir.mkdir(parents=True, exist_ok=True)

    return workflows_dir
