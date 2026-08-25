# src/maxson_build_utils/rendering.py

from __future__ import annotations

from pathlib import Path
from string import Template
import re

_PATTERN = re.compile(r"@@([A-Za-z_][A-Za-z0-9_]*)@@")



def render_template(
    template_path: Path | str,
    context: dict[str, str],
) -> str:
    """Render a text template using the supplied context."""
    template = Template(Path(template_path.read_text()))

    return template.substitute(context)

def render_template_safe(
    template_path: Path | str,
    context: dict[str, str],
) -> str:
    """Render an MBU template using @@name@@ substitutions."""
    text = Path(template_path).read_text()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        try:
            return context[name]
        except KeyError:
            raise KeyError(
                f"Missing template value: {name!r}"
            ) from None

    return _PATTERN.sub(replace, text)
