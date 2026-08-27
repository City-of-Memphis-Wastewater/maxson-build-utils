
# src/maxson_build_utils/scaffold/base/manifest.py

from __future__ import annotations

from pathlib import Path

from ...helpers import WriteResult, write_str_to_file
from ...pyproject import MaxsonPyProject
from ...rendering import get_template_context, render_template

TEMPLATE = '''\
include src/@@import_name@@/data/*
#recursive-include src/@@import_name@@/data/icons *
'''

def run_init_manifest(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Scaffold MANIFEST.in."""
    pyproject = MaxsonPyProject(root_dir)

    context = get_template_context(pyproject)

    text = render_template(
        template_str=TEMPLATE,
        context=context,
    )

    return write_str_to_file(
        path=pyproject.root_dir / "MANIFEST.in",
        text=text,
        overwrite=overwrite,
    )


