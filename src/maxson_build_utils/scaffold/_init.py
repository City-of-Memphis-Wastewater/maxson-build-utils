# src/maxson_build_utils/scaffold/_init.py

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Sequence

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject

# ---------------------------------------------------------------------------
# Template Definition
# ---------------------------------------------------------------------------

INIT_TEMPLATE = Template(
    '''\
#!/usr/bin/env python3
# src/$import_name/__init__.py
from __future__ import annotations

import os

from ._version import __version__

# 1. Clean public-facing mapping
__all__ = [
    "__version__",
$exports_all
    "__gui_easteregg_enabled__",
]


def _check_easteregg_env() -> bool:
    """Helper to dynamically read environment state at call-time."""
    env_flag = os.environ.get("${env_var_prefix}_GUI_EASTEREGG", "").strip().lower()
    return env_flag in ("true", "1", "yes", "on")


# 2. Fully dynamic attribute routing
def __getattr__(name: str):
$getattr_cases
    # Dynamic boolean evaluation for the breadcrumb attribute
    if name == "__gui_easteregg_enabled__":
        return _check_easteregg_env()

    # Dynamic lookups for the GUI function invocation
    if name == "start_gui":

        def _missing_gui():
            raise RuntimeError(
                "start_gui requires pyhabitat and a Tkinter-capable environment"
            )

        _missing_gui.__name__ = "start_gui"
        _missing_gui.__doc__ = (
            "GUI support is unavailable in this environment."
        )

        if _check_easteregg_env():
            try:
                import pyhabitat

                if pyhabitat.tkinter_is_available():
                    from .gui import start_gui

                    return start_gui
            except ImportError:
                pass

        return _missing_gui

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 3. Dynamic introspection reflecting runtime changes
def __dir__():
    exported = list(__all__)
    if _check_easteregg_env():
        exported.append("start_gui")

    return sorted(
        exported
        + [
            "__builtins__",
            "__cached__",
            "__doc__",
            "__file__",
            "__getattr__",
            "__dir__",
            "__loader__",
            "__name__",
            "__package__",
            "__path__",
            "__spec__",
        ]
    )
'''
)


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def _format_all_items(exports: Sequence[str]) -> str:
    """Format custom exported identifiers for __all__ list."""
    if not exports:
        return ""
    return "\n".join(f'    "{item}",' for item in exports) + "\n"


def _format_getattr_cases(exports: dict[str, str]) -> str:
    """Generate if statements for dynamic __getattr__ imports.
    
    exports format: {"export_symbol": "submodule_name"}
    Example: {"copy_then_launch": "core"}
    """
    if not exports:
        return ""

    lines = []
    for symbol, module_name in exports.items():
        lines.append(f'    if name == "{symbol}":')
        lines.append(f"        from .{module_name} import {symbol}")
        lines.append(f"        return {symbol}\n")
    return "\n".join(lines) + "\n"


def derive_env_prefix(import_name: str) -> str:
    """Derive environment variable prefix (e.g. 'copy_n_launch_xlsx' -> 'CNLX')."""
    parts = import_name.split("_")
    if len(parts) > 1:
        return "".join(p[0] for p in parts if p).upper()
    return import_name.upper()


# ---------------------------------------------------------------------------
# Rendering & Entry Points
# ---------------------------------------------------------------------------

def render_init_py(
    import_name: str,
    *,
    exports: dict[str, str] | None = None,
    env_prefix: str | None = None,
) -> str:
    """Render lazy __init__.py content."""
    exports_dict = exports or {}
    prefix = env_prefix or derive_env_prefix(import_name)

    return INIT_TEMPLATE.substitute(
        import_name=import_name,
        env_var_prefix=prefix,
        exports_all=_format_all_items(list(exports_dict.keys())),
        getattr_cases=_format_getattr_cases(exports_dict),
    )


def run_init_init(
    root_dir: Path | str | None = None,
    *,
    exports: dict[str, str] | None = None,
    overwrite: bool = False,
) -> Path:
    """Scaffold __init__.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)
    target_path = pyproject.src_dir / "__init__.py"

    text = render_init_py(
        import_name=pyproject.import_name,
        exports=exports,
    )

    return write_str_to_file(target_path, text=text, overwrite=overwrite)

