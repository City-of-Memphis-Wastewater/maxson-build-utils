# src/maxson_build_utils/scaffold/github_workflows.py

from __future__ import annotations
from pathlib import Path

def run_init_github_workflows(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    root = Path(root_dir or ".").resolve()
    workflow_dir = root / ".github" / "workflows"

    workflows = {
        workflow_dir / "ci.yml": CI_TEMPLATE,
        workflow_dir / "test.yml": TEST_TEMPLATE,
        workflow_dir / "build.yml": BUILD_TEMPLATE,
        workflow_dir / "publish.yml": PUBLISH_TEMPLATE,
        workflow_dir / "docker.yml": DOCKER_TEMPLATE,
        workflow_dir / "flatpak.yml": FLATPAK_TEMPLATE,
        workflow_dir / "deb.yml": DEB_TEMPLATE,
        workflow_dir / "appimage.yml": APPIMAGE_TEMPLATE,
    }

    return [
        write_str_to_file(path, template)
        for path, template in workflows.items()
    ]
