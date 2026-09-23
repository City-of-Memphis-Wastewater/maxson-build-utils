# src/dworshak_prompt/cli.py

"""
"Lazy Loading with Persistence" or a "Configuration Bootstrapper."
Waterfall logic for configuration.
"""
from __future__ import annotations
#from .logging_setup import setup_logging
# Initialize logging before anything else
#logger=setup_logging(verbose=False, debug=False, initial=True)  # Default off
import typer
from rich.console import Console
import os
import sys
from pathlib import Path
from typing import Optional, List
from typer_helptree import add_typer_helptree
import logging

from .multiplexer import DworshakPrompt
from .helpers import PromptMode
from .obtain import Obtain
from ._version import __version__
from .logging_setup import configure_logging_for_application

console = Console() # to be above the tkinter check, in case of console.print
app = typer.Typer()

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"

DEFAULT_PROMPT_MSG = "Enter value"

# --- helper ---

def finalize_protocol_output(
    value: Optional[str],
    emit: bool,
    status_msg: str,
    v_msg: Optional[str] = None
):
    # 1. Human Plane (stderr)
    if status_msg:
        typer.echo(f"[dp] {status_msg}", err=True)
    
    verbose = logging.INFO
    if verbose and v_msg:
        typer.echo(f"VERBOSE: {v_msg}", err=True)

    # 2. Data Plane (stdout)
    if value is not None: # truthy for empty string
        if emit:
            # Raw output for redirection
            # Use sys.stdout.write(value) if you want to avoid the trailing newline
            typer.echo(value)
        else:
            typer.echo("(use --emit to emit value)", err=True)
    else:
        # If we expected a value but got None, signal failure to the shell
        if emit:
            typer.echo("Error: No value to emit.", err=True)
            raise typer.Exit(code=1)

# --- app ---
app = typer.Typer(
    name="dworshak-prompt",
    help=f"Multiplexed user input via console, GUI, and web. (v{__version__})",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"ignore_unknown_options": True,
                      "help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True,no_args_is_help=True)
def main(ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", is_flag=True, help="Show the version."),
    debug: bool = typer.Option(False, "--debug", "-d", is_flag=True, help="Enable diagnostic logging."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Enable detail logging.")
    ):
    """
    Enable --version
    """
    if version:
        typer.echo(__version__)
        raise typer.Exit(code=0)

    # Configure logging immediately
    configure_logging_for_application(debug, verbose)

    # Join the string from the command line arg and log debug to show the command.
    full_command_list = sys.argv
    command_string = " ".join(full_command_list)
    logging.debug(f"command:\n{command_string}\n")

add_typer_helptree(app=app, console=console, version = __version__,hidden=True)

@app.command(name = "ask", help = "Simply prompt for an input. Do not check storage, nor store the input value.")
def ask(
    message: Optional[str] = typer.Option(
        None, "--message", "-m", 
        help="Optional prompt message."
    ),
    interface_priority: Optional[List[PromptMode]] = typer.Option(
        None, "--interface", "-i",
        help="Preferred input modes in order (repeatable, e.g., --interface gui --interface web)."
    ),
    interface_avoid: Optional[List[PromptMode]] = typer.Option(
        None, "--avoid", "-a",
        help="Input modes to avoid (repeatable, e.g., --avoid web --avoid gui)."
    ),
    suggestion: Optional[str] = typer.Option(
        None, 
        "--suggestion", "-s", 
        help="The user will be suggested this value."),

    hide: bool = typer.Option(False, "--hide", "-H", help="Hide input (for passwords)"),
    emit:  bool = typer.Option(False, "--emit", "-e", help="Emit value to stdout.")
):

    if message is None:
        message = DEFAULT_PROMPT_MSG
    interface_priority_list = interface_priority if interface_priority is not None else None
    interface_avoid_set = set(interface_avoid) if interface_avoid is not None else None

    """Get user input and print it to stdout."""
    val = DworshakPrompt().ask(
        message=message,
        interface_priority=interface_priority_list,
        interface_avoid=interface_avoid_set,
        suggestion = suggestion,
        hide_input = hide,
    )

    # truthy for empty string
    status = "Input received." if val is not None else "No input received."
    finalize_protocol_output(val, emit, status)

# Create the 'obtain' sub-app
obtain_app = typer.Typer(help="If a value cannot be retrieved, it will be prompted for and set.")
app.add_typer(obtain_app, name="obtain")

@obtain_app.command(name="secret", help = "Obtain a secret value (Check Vault -> Prompt -> Save).")
def obtain_secret(
    service: str = typer.Argument(..., help="The service name (e.g., maxson-eds)."),
    item: str = typer.Argument(..., help="The item key (e.g., port)."),
    vault_path: Path = typer.Option(None, "--vault-path","-vp", help="Custom encrypted database file path."),
    key_path: Path = typer.Option(None, "--key-path","-kp", help="Custom encryption key file path."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom prompt message."),
    suggestion: Optional[str] = typer.Option(None, "--suggestion", "-s", help="Suggested value."),
    interface_priority: Optional[List[PromptMode]] = typer.Option(
        None, "--interface", "-i",
        help="Preferred input modes in order (repeatable, e.g., --interface gui --interface web)."
    ),
    interface_avoid: Optional[List[PromptMode]] = typer.Option(
        None, "--avoid", "-a",
        help="Input modes to avoid (repeatable, e.g., --avoid web --avoid gui)."
    ),
    forget: bool = typer.Option(False, "--forget", help="Don't save the prompted value."),
    overwrite: bool = typer.Option(False, "--overwrite/--no-overwrite", help="Force a new prompt."),
    emit:  bool = typer.Option(False, "--emit", "-e", help="Emit value to stdout.")
):
    """Obtain a secret value (Check Vault -> Prompt -> Save)."""

    interface_priority_list = interface_priority if interface_priority is not None else None
    interface_avoid_set = set(interface_avoid) if interface_avoid is not None else None
    obtain = Obtain(
            secret_path=vault_path,
            key_path=key_path,
            )
    result = obtain.secret(
        service=service,
        item=item,
        message=message,
        suggestion=suggestion,
        interface_priority=interface_priority_list, 
        interface_avoid=interface_avoid_set, 
        overwrite=overwrite,
        forget=forget
    )

    finalize_protocol_output(result.value, emit, result.status_message)

@obtain_app.command(name="config", help = "Obtain a config value (Check config file -> Prompt -> Save).")
def obtain_config(
    service: str = typer.Argument(..., help="The service name (e.g., maxson-eds)."),
    item: str = typer.Argument(..., help="The item key (e.g., port)."),
    path: Path = typer.Option(None, "--path","-p", help="Custom config file path."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom prompt message."),
    suggestion: Optional[str] = typer.Option(None, "--suggestion", "-s", help="Suggested value."),
    interface_priority: Optional[List[PromptMode]] = typer.Option(
        None, "--interface", "-i",
        help="Preferred input modes in order (repeatable, e.g., --interface gui --interface web)."
    ),
    interface_avoid: Optional[List[PromptMode]] = typer.Option(
        None, "--avoid", "-a",
        help="Input modes to avoid (repeatable, e.g., --avoid web --avoid gui)."
    ),
    overwrite: bool = typer.Option(False, "--overwrite/--no-overwrite", help="Force a new prompt."),
    forget: bool = typer.Option(False, "--forget", help="Don't save the prompted value."),
    emit:  bool = typer.Option(False, "--emit", "-e", help="Emit value to stdout")
):
    interface_priority_list = interface_priority if interface_priority is not None else None
    interface_avoid_set = set(interface_avoid) if interface_avoid is not None else None
    obtain = Obtain(
            config_path=path
            )
    """Get a configuration value (Storage -> Prompt -> Save)."""
    result = obtain.config(
        service=service,
        item=item,
        message=message,
        suggestion=suggestion,
        overwrite=overwrite,
        interface_priority=interface_priority_list,
        interface_avoid=interface_avoid_set,
        forget=forget,
    )

    finalize_protocol_output(result.value, emit, result.status_message)
    
    
    
@obtain_app.command(name="env", help = "Obtain an app setting (Check .env file -> Prompt -> Save).")
def obtain_env(
    key: str = typer.Argument(..., help="The value key (e.g., API_URL)."),
    path: Path = typer.Option(None, "--path","-p", help="Custom .env file path."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom prompt message."),
    suggestion: Optional[str] = typer.Option(None, "--suggestion", "-s", help="Suggested value."),
    interface_priority: Optional[List[PromptMode]] = typer.Option(
        None, "--interface", "-i",
        help="Preferred input modes in order (repeatable, e.g., --interface gui --interface web)."
    ),
    interface_avoid: Optional[List[PromptMode]] = typer.Option(
        None, "--avoid", "-a",
        help="Input modes to avoid (repeatable, e.g., --avoid web --avoid gui)."
    ),
    overwrite: bool = typer.Option(False, "--overwrite/--no-overwrite", help="Force a new prompt."),
    forget: bool = typer.Option(False, "--forget", help="Don't save the prompted value."),
    emit:  bool = typer.Option(False, "--emit", "-e", help="Emit value to stdout")
):
    interface_priority_list = interface_priority if interface_priority is not None else None
    interface_avoid_set = set(interface_avoid) if interface_avoid is not None else None
    obtain = Obtain(
            env_path=path
            )
    """Retrieve a setting; falls back to interactive setup if the key is undefined."""
    result = obtain.env(
        key = key,
        message=message,
        suggestion=suggestion,
        overwrite=overwrite,
        interface_priority=interface_priority_list,
        interface_avoid=interface_avoid_set,
        forget=forget
    )

    finalize_protocol_output(result.value, emit, result.status_message)

if __name__ == "__main__":
    app()

