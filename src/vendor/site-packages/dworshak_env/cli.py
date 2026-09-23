# src/dworshak_env/cli.py
"""
Docstring for dworshak_env.cli
CLI policy:
- Positionals on required arguments. 
- Flags on optional tweaks. 

"""
import typer
#from typer.models import OptionInfo
from rich.console import Console
from rich.table import Table
import os
from pathlib import Path
from typing import Optional

try:
    from typer_helptree import add_typer_helptree
except:
    pass
from .core import DworshakEnv
from ._version import __version__
from .logging_setup import configure_logging_for_application

console = Console(stderr=True)

app = typer.Typer()

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"

app = typer.Typer(
    name="dworshak-env",
    help=f"Store and retrieve plaintext, single-key configuration values to typical .env file. (v{__version__})",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"ignore_unknown_options": True,
                      "help_option_names": ["-h", "--help"]},
)

add_typer_helptree(app=app, console=console, version = __version__,hidden=True)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", is_flag=True, help="Show the version."),
    debug: bool = typer.Option(False, "--debug", "-d", is_flag=True, help="Enable diagnostic logging."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Enable detail logging.")
    ):
    """
    Enable --version
    """
    if version:
        typer.echo(__version__, err=False)
        raise typer.Exit(code=0)

    configure_logging_for_application(debug,verbose)

@app.command()
def get(
    key: str = typer.Argument(..., help="The value key (e.g., PORT, API_KEY)."),
    path: Path = typer.Option(None, "--path","-p", help="Custom .env file path."),
):
    """
    Get a .env configuration value (single-key).
    """
    env_mgr = DworshakEnv(path=path)
    value = env_mgr.get(key=key)
    
    if value is not None:
        typer.echo(value) # raw value → stdout for capture
    else:
        # Errors go to stderr so they don't get captured in variables
        typer.echo(f"Error: key '{key}' not found", err=True)
        raise typer.Exit(code=1)

@app.command()
def set(
    key: str = typer.Argument(..., help="The key (e.g. PORT, API_KEY)."),
    value: str = typer.Argument(...,help="The value to store."),
    path: Path = typer.Option(None, "--path","-p", help="Custom config file path."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing value."),
):
    """
    Store or update a .env configuration value (single-key).
    """
    if value is None:
        typer.echo(f"Provided: None. No value saved.", err=True)
        raise typer.Exit(code=1)
    env_mgr = DworshakEnv(path=path)
    existing_value = env_mgr.get(key=key)

    # If it exists and we aren't overwriting, print value and exit
    if existing_value is not None and not overwrite:
        typer.echo(f"Key [{key}] already exists. Use --overwrite.", err=True)
        # Send raw value to stdout
        typer.echo(existing_value)
        raise typer.Exit(code=1)

    # Trigger the prompt or the direct set
    final_value = env_mgr.set(
        key=key,
        value=value,
        overwrite=overwrite
    )

    if final_value is not None:
        # Status message goes to stderr
        typer.echo(f"Stored [{key}] successfully.", err=True)
        # ONLY the value goes to stdout
        typer.echo(final_value)
    else:
        # Error context to stderr
        typer.echo(f"Error: Failed to set value for [{key}]", err=True)
        
        raise typer.Exit(code=1)

@app.command()
def remove(
    key: str = typer.Argument(..., help="Value key."),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Custom .env file path."),
    fail: bool = typer.Option(False, "--fail", help="Raise error if config not found"),
    yes: bool = typer.Option(
        False,
        "--yes","-y",
        is_flag=True,
        help="Skip confirmation prompt (useful in scripts or automation)"
    ),
):
    """Remove a setting from the target .env file."""

    env_mgr = DworshakEnv(path=path)

    if not yes:
        yes = typer.confirm(
            f"Are you sure you want to remove value for key: {key}?",
            default=False,  # ← [y/N] style — safe default
        )
    if not yes:
        console.print("[yellow]Operation cancelled.[/yellow]")
        raise typer.Exit(code=0)

    deleted = env_mgr.remove(key)
    if deleted:
        console.print(f"[green]Removed value for key: {key}[/green]")
    else:
        if fail:
            raise KeyError(f"No value found for key: {key}")
        console.print(f"[yellow]No value found for key: {key}[/yellow]")


@app.command(name = "list")
def list_entries(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Custom .env file path."),
):
    """List all stored settings."""
    env_mgr = DworshakEnv(path=path)
    #keys = env_mgr.list_entries()

    # Use the load() to get the full dict for efficiency
    data = env_mgr.load()

    table = Table(title=f"Stored Env Vars ({env_mgr.path})")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green") # Changed to green for visual distinction
    
    # Sort keys for a predictable CLI output
    for key in sorted(data.keys()):
        table.add_row(key, data[key])
        
    console.print(table)

if __name__ == "__main__":
    app()

