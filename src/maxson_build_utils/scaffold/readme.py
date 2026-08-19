# src/maxson_build_utils/scaffold/readme.py
"""
Readme.md should be generated to include the description (which may or may not exist yet but might be the only thing prompted for), and should include the helptree reference section.
"""
from __future__ import annotations

from pathlib import Path
from string import Template

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject


README_TEMPLATE = Template(
    """\
# $pretty_name

$description

## Helptree

See the `$app_name` Typer CLI structure.

```bash
$app_name helptree
```
""" )
def run_init_readme( root_dir: Path | str | None = None, ) -> Path: """Create the project README.""" pyproject = MaxsonPyProject(root_dir)
    description = pyproject.description or ""

    text = README_TEMPLATE.substitute(
        pretty_name=pyproject.pretty_name,
        description=description,
        app_name=pyproject.app_name,
    )

    return write_str_to_file(
        pyproject.root_dir / "README.md",
        text=text,
    )
