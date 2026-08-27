# src/maxson_build_utils/rendering.py
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
    *,
    context: dict[str, Any],
    template_str: str | None = None,
    template_path: Path | None = None,
) -> str:
    """Render an MBU template from a string or file."""
    if (template_str is None) == (template_path is None):
        raise ValueError(
            "Exactly one of template_str or template_path must be provided."
        )

    text = (
        template_str
        if template_str is not None
        else template_path.read_text()
    )

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)

        try:
            return str(context[name])
        except KeyError:
            raise KeyError(
                f"Missing template value: {name!r}"
            ) from None

    return _PATTERN.sub(replace, text)
