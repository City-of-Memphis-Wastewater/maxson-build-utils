# src/maxson_build_utils/scaffold/ci/github/render.py

from __future__ import annotations

from pathlib import Path

from ....rendering import render_template_safe, render_template
from ....helpers import WriteResult, write_str_to_file
from ....pyproject import MaxsonPyProject


TEMPLATE_DIR = Path(__file__).parent / "templates"

"""
ls src/maxson_build_utils/scaffold/ci/github/templates/workflows
appimage.yml      docker.yml            package-deb.yml  theory.yml
build-onedir.yml  flatpak.yml           publish.yml
ci.yml            package-appimage.yml  test.yml
"""

def run_init_github_workflows(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    root = Path(root_dir or ".").resolve()
    pyproject = MaxsonPyProject(root)

    workflow_dir = root / ".github" / "workflows"

    context = {
        "app_name": pyproject.app_name,
        "pretty_name": pyproject.pretty_name,
        "import_name": pyproject.import_name,
    }

    workflows = {
        workflow_dir / "ci.yml":
            TEMPLATE_DIR / "workflows" / "ci.yml",

        workflow_dir / "test.yml":
            TEMPLATE_DIR / "workflows" / "test.yml",

        workflow_dir / "pyinstaller-onedir.yml":
            TEMPLATE_DIR / "workflows" / "pyinstaller-onedir.yml",

        workflow_dir / "publish.yml":
            TEMPLATE_DIR / "workflows" / "publish.yml",

        workflow_dir / "docker.yml":
            TEMPLATE_DIR / "workflows" / "docker.yml",

        workflow_dir / "flatpak.yml":
            TEMPLATE_DIR / "workflows" / "flatpak.yml",

        workflow_dir / "deb.yml":
            TEMPLATE_DIR / "workflows" / "deb.yml",

        workflow_dir / "appimage.yml":
            TEMPLATE_DIR / "workflows" / "appimage.yml",
    }

    results = []

    for target_path, template_path in workflows.items():
        text = render_template_safe(template_path, context)
        results.append(write_str_to_file(target_path, text))

    return results

def run_init_github_ci(
    root_dir: Path | str | None = None,
) -> list[WriteResult]:
    results = []

    results.extend(run_init_github_workflows(root_dir))
    results.append(run_init_dependabot(root_dir))

    return results

def run_init_dependabot(
    root_dir: Path | str | None = None,
) -> WriteResult:
    root = Path(root_dir or ".").resolve()

    target = root / ".github" / "dependabot.yml"
    template = TEMPLATE_DIR / "dependabot.yml"

    context = {} # no context required, just copy

    text = render_template(template, context)

    return write_str_to_file(target, text)
