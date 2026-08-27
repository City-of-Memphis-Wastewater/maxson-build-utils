# src/maxson_build_utils/scaffold/cli.py

from __future__ import annotations

from pathlib import Path

from ..helpers import WriteResult, write_str_to_file
from ..pyproject import MaxsonPyProject
from ..rendering import get_template_context, render_template


CLI_TEMPLATE = '''\
#!/usr/bin/env python3
# src/@@import_name@@/cli.py

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from typer_helptree import add_typer_helptree

from ._version import __version__
from .context import APP_NAME, DESCRIPTION_STR
from .logging_setup import (
    configure_logging_all_debug,
    configure_logging_for_application,
)

logger = logging.getLogger(__name__)

console_stderr = Console(stderr=True)
console_stdout = Console()

# Force Rich to always enable colors, even when running from a .pyz bundle.
os.environ["FORCE_COLOR"] = "1"

# Optional but helpful for full terminal feature detection.
os.environ["TERM"] = "xterm-256color"

app = typer.Typer(
    name=APP_NAME,
    help=f"{DESCRIPTION_STR} (v{__version__})",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "help_option_names": ["-h", "--help"],
    },
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show application version and exit.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug level logs for app.",
    ),
    all_debug: bool = typer.Option(
        False,
        "--all-debug",
        help="Enable debug logs for app AND dependencies.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose info level logs.",
    ),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="Custom path to output log file.",
    ),
):
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    if all_debug:
        configure_logging_all_debug()
    else:
        configure_logging_for_application(
            debug=debug,
            verbose=verbose,
            log_to_file=log_file is not None,
        )

    logger.debug("Executing command: %s", " ".join(sys.argv))

    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        typer.echo(ctx.get_help())
        raise typer.Exit()


add_typer_helptree(
    app=app,
    console=console_stderr,
    version=__version__,
    hidden=False,
)


@app.command(name="placeholder")
def placeholder(
    path: Path = Path("path"),
):
    """Placeholder."""
    console_stderr.print(f"{path=}")


if __name__ == "__main__":
    app()
'''


def run_init_cli(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Scaffold cli.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)

    context = get_template_context(pyproject)

    text = render_template(
        template_str=CLI_TEMPLATE,
        context=context,
    )

    return write_str_to_file(
        path=pyproject.src_dir / "cli.py",
        text=text,
        overwrite=overwrite,
    )


