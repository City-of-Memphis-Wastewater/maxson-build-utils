#!/usr/bin/env python3 
# SPDX-License-Identifier: MIT
# src/typer_helptree/cli.py
from __future__ import annotations
import typer
from rich.console import Console
from typing import Dict, Optional, Union, List
import pyhabitat
import sys
import os
from importlib.resources import files

from typer_helptree._version import __version__

APP_NAME = "typer-helptree"
APP_DIR = "typer_helptree"

console = Console() # to be above the tkinter check, in case of console.print

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"

app = typer.Typer(
    name=APP_NAME,
    help=f"Visualize your entire CLI, beautifully. (v{__version__})",
    add_completion=False,
    invoke_without_command = True, 
    no_args_is_help = True,
    context_settings={"ignore_unknown_options": True,
                      "allow_extra_args": True,
                      "help_option_names": ["-h", "--help"]},
)


@app.callback()
def main(ctx: typer.Context,
    version: Optional[bool] = typer.Option(
    None, "--version", is_flag=True, help="Show the version."
    )
    ):
    """
    Main.
    """
    if version:
        typer.echo(__version__)
        raise typer.Exit(code=0)
        
    if ctx.invoked_subcommand is None:
        pass
        raise typer.Exit(code=0)


from typer_helptree.cli_helptree import add_typer_helptree
add_typer_helptree(app=app, console=console, version = __version__,hidden=False)

# Create tools sub-group
tools_app = typer.Typer(help="Additional utility features and maintenance tools.")
app.add_typer(tools_app, name="tools")

@tools_app.command(name="nested-tool")
def tools_nested_tool():
    """Demo"""
    print("This is a demo of a nested command.", file=sys.stderr)

@tools_app.command(name="browse-exports")
def tools_browse_exports():
    """Open the system file explorer at the report output directory."""
    from typer_helptree.io import get_export_path
    
    target_dir = get_export_path()
    console.print(f"Opening: [bold cyan]{target_dir}[/bold cyan]")
    
    try:
        pyhabitat.show_system_explorer(path = target_dir)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(name="docs", help="Show the docs for this software.")
def docs_command(
    license: Optional[bool] = typer.Option(
        None, "--license", "-l", help="Show the LICENSE text."
    ),
    readme: Optional[bool] = typer.Option(
        None, "--readme", "-r", help="Show the README.md content."
    ),
):
    """
    Show docs for the package.
    """
    if not license and not readme:
        # If no flags are provided, show the help message for the docs subcommand.
        # Use ctx.invoke(ctx.command.get_help, ctx) if you want to print help immediately.
        # Otherwise, the default behavior (showing help) works fine, but we'll add a message.
        console.print("[yellow]Please use either the --license flag and/or the --readme flag to print.[/yellow]")
        return # Typer will automatically show the help message.

    if pyhabitat.is_in_git_repo():
        """This is too aggressive. But we don't expect it often. Probably worth it."""
        from typer_helptree.datacopy import ensure_data_files_for_build
        ensure_data_files_for_build()

    # --- Handle --license flag ---
    if license:
        try:
            license_path = files(f"{APP_DIR}.data") / "LICENSE"
            license_text = license_path.read_text(encoding="utf-8")
            console.print(f"\n[bold green]=== LICENSE ===[/bold green]")
            console.print(license_text, highlight=False)

        except FileNotFoundError:
            console.print("[bold red]Error:[/bold red] The embedded license file could not be found.")
            raise typer.Exit(code=1)

    # --- Handle --readme flag ---
    if readme:
        try:
            readme_path = files(f"{APP_DIR}.data") / "README.md"
            readme_text = readme_path.read_text(encoding="utf-8")

            # Using rich's Panel can frame the readme text nicely
            console.print(f"\n[bold green]=== README ===[/bold green]")
            console.print(readme_text, highlight=False)

        except FileNotFoundError:
            console.print("[bold red]Error:[/bold red] The embedded README.md file could not be found.")
            raise typer.Exit(code=1)

    # Exit successfully if any flag was processed
    raise typer.Exit(code=0)

if __name__ == "__main__":
    app()
    
