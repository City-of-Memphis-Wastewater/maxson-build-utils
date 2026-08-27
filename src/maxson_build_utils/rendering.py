# src/maxson_build_utils/rendering.py
'''
from __future__ import annotations

from pathlib import Path
from string import Template
import re

_PATTERN = re.compile(r"@@([A-Za-z_][A-Za-z0-9_]*)@@")


def render_template(
    template_path: Path,
    context: dict[str, str],
) -> str:
    """Render a text template using the supplied context."""
    #template = Template(Path(template_path.read_text()))
    template = Template(template_path.read_text())

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

# --- 

def get_template_values(
    pyproject: MaxsonPyProject,
    ) -> dict[str, object]:
    return {
        "app_name": pyproject.app_name,
        "pretty_name": pyproject.pretty_name,
        "import_name": pyproject.import_name,
        "description": get_description(pyproject),
        "log_path": get_log_path(pyproject),
     }

#
'''
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .pyproject import MaxsonPyProject


_PATTERN = re.compile(r"@@([A-Za-z_][A-Za-z0-9_]*)@@")


def get_template_context(
    pyproject: MaxsonPyProject,
) -> dict[str, Any]:
    """Return the standard context available to MBU templates."""
    return {
        "app_name": pyproject.app_name,
        "pretty_name": pyproject.pretty_name,
        "import_name": pyproject.import_name,
        "description": (
            pyproject.get("project", "description")
            or pyproject.pretty_name
        ),
    }


def render_template(
    context: dict[str, Any],
    template_str: str | None = None,
    template_path: Path | None = None,
) -> str:
    """Render an MBU template using @@name@@ substitutions."""
    if template_str is None and template_path is None:
        return None
    elif template_str is not None:
        text = template_str
    elif template_path is not None:
        text = template_path.read_text()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)

        try:
            return str(context[name])
        except KeyError:
            raise KeyError(
                f"Missing template value: {name!r}"
            ) from None

    return _PATTERN.sub(replace, text)
