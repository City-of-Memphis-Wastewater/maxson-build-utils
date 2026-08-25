# src/maxson_build_utils/rendering.py

from __future__ import annotations

from pathlib import Path
from string import Template


def render_template(
    template_path: Path | str,
    context: dict[str, str],
) -> str:
    """Render a text template using the supplied context."""
    template = Template(Path(template_path.read_text()))

    return template.substitute(context)
