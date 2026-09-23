# src/dworshak_config/cli.py
import typer
from typer.models import OptionInfo
from rich.console import Console
from rich.table import Table
import os
from pathlib import Path
from typing import Optional

try:
    from typer_helptree import add_typer_helptree
except:
    pass
from .core import DworshakConfig
from ._version import __version__
from .logging_setup import configure_logging_for_application

console = Console(stderr=True)
app = typer.Typer()

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"

app = typer.Typer(
    name="dworshak-config",
    help=f"Store and retrieve plaintext two-key configuration values to JSON. (v{__version__})",
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

    configure_logging_for_application(debug, verbose)

add_typer_helptree(app=app, console=console, version = __version__,hidden=True)

@app.command()
def get(
    service: str = typer.Argument(..., help="The service name (e.g., Maxson)."),
    item: str = typer.Argument(..., help="The item key (e.g., port)."),
    path: Path = typer.Option(None, "--path","-p", help="Custom config file path."),
    ):
    """
    Get a configuration value (vault-style, two-key).
    """
    config_mngr = DworshakConfig(path=path)
    
    value = config_mngr.get(
        service=service,
        item=item,
    )
    if value is not None:
        # Only print the value to stdout for piping/capture
        typer.echo(value)

@app.command()
def set(
    service: str = typer.Argument(..., help="The service name (e.g., Maxson)."),
    item: str = typer.Argument(..., help="The item key (e.g., port)."),
    value: str = typer.Argument(..., help="Directly set a value."),
    path: Path = typer.Option(None, "--path","-p", help="Custom config file path."),
    overwrite: bool = typer.Option(True, "--overwrite/--no-overwrite", help="Force a new prompt."),
    ):
    """
    Set a configuration value (vault-style, two-key).
    """
    config_mngr = DworshakConfig(path=path)
    
    # Let the core class handle overwrite protection
    config_mngr.set(
        service=service,
        item=item,
        value=value,
        overwrite=overwrite,
    )

    # Read back what is actually stored now and print it
    final_value = config_mngr.get(service, item)
    if final_value is not None:
        typer.echo(final_value)
    else:
        # Shouldn't happen after successful set, but defensive
        console.print("[red]Failed to read back value[/red]", err=True)
        raise typer.Exit(code=1)

@app.command()
def remove(
    service: str = typer.Argument(..., help="Service name."),
    item: str = typer.Argument(..., help="Item key."),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Custom config file path."),
    fail: bool = typer.Option(False, "--fail", help="Raise error if config not found"),
    yes: bool = typer.Option(
        False,
        "--yes","-y",
        is_flag=True,
        help="Skip confirmation prompt (useful in scripts or automation)"),
    ):
    """Remove a config value."""

    config_manager = DworshakConfig(path=path)
    
    if not yes:
        yes = typer.confirm(
            f"Are you sure you want to remove {service}/{item}?",
            default=False,  # ← [y/N] style — safe default
        )
    if not yes:
        console.print("[yellow]Operation cancelled.[/yellow]")
        raise typer.Exit(code=0)

    deleted = config_manager.remove(service, item)
    if deleted:
        console.print(f"[green]Removed value {service}/{item}[/green]")
    else:
        if fail:
            raise KeyError(f"No value found for {service}/{item}")
        console.print(f"[yellow]No value found for {service}/{item}[/yellow]")


@app.command(name = "list")
def list_entries(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Custom config file path."),
    ):
    """List all stored values in a given config file."""
    config_manager = DworshakConfig(path=path)
    
    # Access the raw data for efficient listing of values
    # Assuming DworshakConfig follows the same _load() pattern
    data = config_manager.load()
    
    table = Table(title=f"Stored Values ({config_manager.path})")
    table.add_column("Service", style="cyan")
    table.add_column("Item", style="green")
    table.add_column("Value", style="yellow")
    
    # Nested iteration: Service -> Items
    for service in sorted(data.keys()):
        service_data = data[service]
        for item in sorted(service_data.keys()):
            value = str(service_data[item])
            table.add_row(service, item, value)
            
    console.print(table)

if __name__ == "__main__":
    app()

