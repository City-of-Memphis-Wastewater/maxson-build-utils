# src/maxson_build_utils/scaffold_cli.py
from __future__ import annotations
from .helpers import write_str_to_file
from .pyproject import PyProject

pyproject = PyProject()
def run_init_cli( ):
    write_str_to_file(pyproject.src_dir / "cli.py", text = raw_cli_str)

raw_cli_str = '''
#!/usr/bin/env python3
# src/__IMPORT_NAME__/cli.py
import os
import sys
import typer
from pathlib import Path
from typer_helptree import add_typer_helptree
from rich.console import Console
import logging

from .context import DESCRIPTION_STR, APP_NAME
from ._version import __version__
from .logging_setup import configure_logging_for_application

console_stderr = Console(stderr=True)
console_stdout = Console()

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"


app = typer.Typer(
    name=APP_NAME,
    help=f"{DESCRIPTION_STR} (v{__version__})",
    add_completion=False,
    invoke_without_command = True,
    no_args_is_help = True,
    context_settings={"ignore_unknown_options": True,
                      "allow_extra_args": True,
                      "help_option_names": ["-h", "--help"]},
)

@app.callback(invoke_without_command=True, no_args_is_help=False)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", is_flag=True),
    debug: bool = typer.Option(False, "--debug","-d", is_flag=True),
    verbose: bool = typer.Option(False, "--verbose","-v", is_flag=True),
):
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    configure_logging_for_application(debug,verbose)

    # Join the string from the command line arg and log debug to show the command.
    full_command_list = sys.argv
    command_string = " ".join(full_command_list)
    logging.debug(f"command:\n{command_string}\n")


add_typer_helptree(app = app, console = console_stderr, version = __version__, hidden = False)


@app.command(name="placeholder")
def placeholder(
    path: Path = Path("path")
):
    """Placeholder"""
    console_stderr.print(f"{path=}")


if __name__ == "__main__":
    app()
'''
raw_cli_str = raw_cli_str.replace("__IMPORT_NAME__", pyproject.import_name)
