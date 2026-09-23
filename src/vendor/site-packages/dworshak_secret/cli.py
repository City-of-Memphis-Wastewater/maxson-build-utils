# src/dworshak_secret/cli.py
from __future__ import annotations
import pyhabitat
import typer
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler
from click.exceptions import Abort
from pathlib import Path
from typing import Optional
from typer_helptree import add_typer_helptree
import logging

from .logging_setup import configure_logging_for_application
from ._version import __version__

# sentinel value to allow empty strings to be passed
MISSING = object()

console = Console(stderr=True)

# Force Rich to always enable colors, even in .pyz or Termux
os.environ["FORCE_COLOR"] = "1"
os.environ["TERM"] = "xterm-256color"

def print_prompt_hint(service:str="SERVICE",item:str="ITEM"):
    console.print(
        "[yellow]Secret not provided.[/yellow]\n\n"
        "If running inside command substitution or scripts, use:\n\n"
        f"  dworshak prompt obtain secret {service} {item} --emit\n"
    )
    
app = typer.Typer(
    name="dworshak-secret",
    help =f"Store and retrieve plaintext two-key credential values to encrypted database file. (v{__version__})",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "help_option_names": ["-h", "--help"]
    },
)

# Create the sub-apps
vault_app = typer.Typer(help="Manage the vault infrastructure and security.")


# Add vault app to the main secret app
app.add_typer(vault_app, name="vault")

# In cli.py
add_typer_helptree(app=app, console=console, version = __version__,hidden=False)


# 1. Check for crypto before importing vault logic
try:
    import cryptography
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# 2. Define the help message here or import it
MSG_CRYPTO_HELP_MSG = """
[yellow]Encryption is not available. Install with crypto extra:[/yellow]
  uv add "dworshak-secret[crypto]"
  or
  pip install "dworshak-secret[crypto]"

On Termux, use "pkg add python-cryptography"
On iSH alpine, use "apk add py3-cryptography"
"""

def crypto_instructions():
    if not CRYPTO_AVAILABLE:
        from rich.console import Console
        Console(stderr=True).print(MSG_CRYPTO_HELP_MSG)
        raise typer.Exit(code=1)
                
from .core import DworshakSecret
from .actions import import_records
from .errors import WrongKeyError

@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", is_flag=True, help="Show the version."),
    debug: bool = typer.Option(False, "--debug", "-d", is_flag=True, help="Enable diagnostic logging."),
    verbose: bool = typer.Option(False, "--verbose", "-v", is_flag=True, help="Enable detail logging.")
    ):
    """
    Enable --version and --debug
    """ 
    if version:
        typer.echo(__version__)
        raise typer.Exit(code=0)

    configure_logging_for_application(debug, verbose)
    
    if ctx.invoked_subcommand not in [None]:
        crypto_instructions()
        
@vault_app.command()
def setup(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path.")
    ):
    """Initialize vault and encryption key."""
    secret_manager = DworshakSecret(db_path=path, key_path=key_path)
    res = secret_manager.initialize_vault()
    
    #res = initialize_vault(db_path=path, key_path=key_path)    
    if res.success:
        # Use Panel.fit for that premium CLI feel
        color = "green" if res.is_new else "blue"
        title = "Success"
        
        console.print(Panel.fit(res.message, title=title, border_style=color))
    else:
        # Standard error reporting
        console.print(Panel.fit(res.message, title="Error", border_style="red"))
        raise typer.Exit(code=1)

@app.command()
def set(
    service: str = typer.Argument(..., help="Service name."),
    item: str = typer.Argument(..., help="Item key."),
    secret: Optional[str] = typer.Argument(
        None,
        help="The secret value. If omitted in interactive mode → prompt with hidden input."
    ),
    emit: bool = typer.Option(False, "--emit","-e",help ="Emit the value to stdout."),
    empty: bool = typer.Option(False, "--empty", help="Store an empty string."),
    path: Path = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    overwrite: bool = typer.Option(False, "--overwrite/--no-overwrite", help="Force a value setting even if one already exists.")
):
    """Store a new credential in the vault."""

    secret_manager = DworshakSecret(db_path=path, key_path=key_path)
    
    #existing_secret = secret_manager.get(service, item)
    try:
        existing_secret = secret_manager.get(service=service, item=item)
    except WrongKeyError as e:
        # Print the error cleanly using your console object
        console.print(f"[bold red]WrongKeyError:[/bold red] {e}")
        # Exit with a status code but NO traceback
        raise typer.Exit(code=1)
    
    if existing_secret is not None:
        if not overwrite:
            console.print(f"Credential for {service}/{item} exists. Use --overwrite flag. ")
            raise typer.Exit(code = 0)
    if empty:
        secret = ""
    elif secret is None:
        if not sys.stdin.isatty():
            # Handle piped input: echo "val" | dworshak-secret set ...
            #secret = sys.stdin.read().strip()
            data = sys.stdin.read().strip()
            if not data:
                print_prompt_hint()
                raise typer.Exit(1)
            secret = data
        elif not pyhabitat.is_likely_ci_or_non_interactive():
            try:
                secret = typer.prompt(f"Enter secret for {service}/{item}", hide_input=True)
            except (KeyboardInterrupt,EOFError,Abort):
                console.print("\n[yellow]Prompt cancelled by user (Ctrl+C).[/yellow]")
                raise typer.Exit(1)
            except Exception:
                console.print("[yellow]Interactive prompt failed.[/yellow]")
                print_prompt_hint()
                raise typer.Exit(1)
        else:
            # wrapped assignment lands here
            print_prompt_hint(service, item)
            raise typer.Exit(code=1)
    
    status = secret_manager.check_vault()
    if not status.is_valid:
        console.print(f"status.is_valid = {status.is_valid}")
        console.print(f"status.message = {status.message}")
        raise typer.Exit(code=0)
    
    if overwrite and (service, item) in secret_manager.list_contents():
        console.print(f"[yellow]Overwriting credential {service}/{item}[/yellow]")
    
    secret_manager.set(service = service, item = item, value = secret, overwrite=overwrite)
    console.print(f"[green]Credential for {service}/{item} stored securely.[/green]")
    if emit:
        typer.echo(secret) #, nl=False) # nl=False prevents trailing newlines
    else:
        typer.echo("(use --emit to emit value)", err=True)
    

@app.command()
def get(
    service: str = typer.Argument(..., help="Service name."),
    item: str = typer.Argument(..., help="Item key."),
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    fail: bool = typer.Option(False, "--fail", help="Raise error if missing"),
    emit: bool = typer.Option(False, "--emit","-e",help ="Emit the value to stdout.")
):
    """Retrieve a credential from the vault."""
    
    secret_manager = DworshakSecret(db_path=path, key_path=key_path)
    status = secret_manager.check_vault()
    
    if not status.is_valid:
        console.print(f"status.is_valid = {status.is_valid}")
        console.print(f"status.message = {status.message}")
        raise typer.Exit(code=0)
    

    try:
        existing_secret = secret_manager.get(service=service, item=item, fail=fail)
    except WrongKeyError as e:
        # Print the error cleanly using your console object
        console.print(f"[bold red]WrongKeyError:[/bold red] {e}")
        # Exit with a status code but NO traceback
        raise typer.Exit(code=1)

    if existing_secret is None:
        typer.echo(f"No credential found for {service}/{item}", err=True)
        raise typer.Exit(code=0)
    else:
        typer.echo(f"Credential found for {service}/{item} ", err=True)
    if emit:
        typer.echo(existing_secret) #, nl=False) # nl=False prevents trailing newlines
    else:
        typer.echo("(use --emit to emit value)", err=True)
    
@app.command()
def remove(
    service: str = typer.Argument(..., help="Service name."),
    item: str = typer.Argument(..., help="Item key."),
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    yes: bool = typer.Option(
        False,
        "--yes","-y",
        is_flag=True,
        help="Skip confirmation prompt (useful in scripts or automation)."
    ),
    fail: bool = typer.Option(False, "--fail", help="Raise error if secret not found")
):
    """Remove a credential from the vault."""
    secret_manager = DworshakSecret(db_path=path, key_path=key_path)
    status = secret_manager.check_vault()
    
    if not status.is_valid:
        console.print(f"status.is_valid = {status.is_valid}")
        console.print(f"status.message = {status.message}")
        raise typer.Exit(code=0)
    
    existing_secret = secret_manager.get(service=service, item=item, fail=fail)
    if existing_secret is None:
        typer.echo(f"No credential found for {service}/{item}", err=True)
        raise typer.Exit(code=0)

    if not yes: 
        yes = typer.confirm(
        f"Are you sure you want to remove {service}/{item}?",
        default=False,  # ← [y/N] style — safe default
        )

    if not yes:
        raise typer.Exit(code=0)

    deleted = secret_manager.remove(service, item)
    if deleted:
        console.print(f"[green]Removed credential {service}/{item}[/green]")
    else:
        if fail:
            raise KeyError(f"No credential found for {service}/{item}")
        console.print(f"[yellow]No credential found for {service}/{item}[/yellow]")


@app.command(name = "list")
def list_entries(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
):
    """List all stored credentials."""
    secret_manager = DworshakSecret(db_path=path)
    status = secret_manager.check_vault()
    
    if not status.is_valid:
        console.print(f"status.is_valid = {status.is_valid}")
        console.print(f"status.message = {status.message}")
        raise typer.Exit(code=0)
    
    creds = secret_manager.list_contents()
    table = Table(title="Stored Credentials")
    table.add_column("Service", style="cyan")
    table.add_column("Item", style="green")
    for service, item in creds:
        table.add_row(service, item)
    console.print(table)

@vault_app.command()
def health(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    ):
    """Check vault integrity and permissions."""
    secret_manager = DworshakSecret(db_path=path)
    vault_status = secret_manager.check_vault()
    console.print(vault_status)

    if key_path:
        key_status = secret_manager.check_key_file()
        console.print(key_status)

@vault_app.command()
def export(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    output_path: Optional[Path] = typer.Option(
        None, 
        "--output", "-o", 
        help="Path to save the export."
    ),
    decrypt: bool = typer.Option(
        False, 
        "--decrypt", 
        is_flag=True, 
        help="Export the file with the secrets decrypted."
    ),
    yes: bool = typer.Option(
        False,
        "--yes","-y",
        is_flag=True,
        help="Skip confirmation prompt (useful in scripts or automation)."
    )
):  
    """
    Export the current vault to a JSON file.
    """
    # export_vault handles default paths internally if output_path is None
    if decrypt and not yes:
        yes = typer.confirm(
        f"Are you sure you want to decrypted secrets in the export?",
        default=False,  # ← [y/N] style — safe default
        )
    secret_manager = DworshakSecret(db_path=path,key_path=key_path)
    status = secret_manager.check_vault()
    
    final_path = secret_manager.export_vault(
        output_path=output_path, 
        decrypt=decrypt,
        yes=yes
        )
    
    if final_path:
        console.print(f"[green]Success![/green] Your vault has been exported to: [bold]{final_path}[/bold]")
    else:
        console.print("[red]Export failed.[/red] Check logs for details.")

@vault_app.command(name="import") # 'import' is a reserved keyword in Python
def import_cmd(
    json_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to the JSON file to import."
    ),
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault DB path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    overwrite: bool = typer.Option(
        False, 
        "--overwrite", 
        is_flag=True, 
        help="If new credentials match existing ones, overwrite them."
    )
): 
    """
    Import a properly structured JSON file into the Dworshak vault.
    """
    # import_records returns a dict of stats: {"added": x, "updated": y, "skipped": z}

    secret_manager = DworshakSecret(db_path=path,key_path=key_path)
    status = secret_manager.check_vault()
    
    stats = secret_manager.import_records(client=secret_manager,json_path = json_path, overwrite=overwrite)
    #stats = import_records(json_path = json_path, db_path = path, overwrite=overwrite)
    
    if stats:
        console.print(f"\n[bold]Import Summary for {path.name}:[/bold]")
        console.print(f"  [green]Added:[/green]   {stats['added']}")
        console.print(f"  [yellow]Updated:[/yellow] {stats['updated']}")
        console.print(f"  [blue]Skipped:[/blue] {stats['skipped']}")
    else:
        console.print("[red]Import failed or rejected.[/red]")


@vault_app.command(name="rotate-key")
def rotate_key_cmd(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault path."),
    key_path: Optional[Path] = typer.Option(None, "--key-path", "-kp", help="Custom key path."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        is_flag=True,
        help="Simulate the rotation without making any changes or backups",
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        is_flag=True,
        help="Skip automatic backup (advanced / dangerous; ignored in dry-run)",
    ),
):
    """Rotate the encryption key and re-encrypt all stored secrets.

    WARNING: This is a destructive operation unless --dry-run is used.
    A backup is created automatically unless --no-backup is specified.
    Use --dry-run first to preview what will happen.
    """
    secret_manager = DworshakSecret(db_path=path,key_path=key_path)
    status = secret_manager.check_vault()
    
    success, message, affected = secret_manager.rotate_key(
        dry_run=dry_run,
        auto_backup=not no_backup if not dry_run else False,
    )

    if success:
        if dry_run:
            console.print("[cyan]Dry run completed – no changes were made.[/cyan]")
        else:
            console.print("[green]Key rotation completed successfully.[/green]")

        console.print(message)

    else:
        console.print(f"[red]Operation failed:[/red] {message}")
        raise typer.Exit(1)

@vault_app.command()
def backup(
    path: Optional[Path] = typer.Option(None, "--vault-path", "-vp", help="Custom vault file path."),
    extra_suffix: str = typer.Option(
        "",
        "--suffix", "-s",
        help="Extra identifier in the filename (e.g. 'pre-import', 'manual', 'test')."
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir", "-o",
        help="Custom directory to save the backup (default: same as vault.db)."
    ),
    no_timestamp: bool = typer.Option(
        False,
        "--no-timestamp",
        is_flag=True,
        help="Omit timestamp from filename (not recommended unless you know what you're doing)."
    ),
):
    """Create a timestamped backup copy of the vault database."""
    secret_manager = DworshakSecret(db_path=path)
    status = secret_manager.check_vault()
    
    if not status.is_valid:
        console.print(f"[red]Vault unhealthy: {status.message}[/red]")
        raise typer.Exit(1)

    # Call the library function
    backup_path = secret_manager.backup_vault(
        extra_suffix=extra_suffix,
        include_timestamp=not no_timestamp,
        dest_dir=output_dir,
    )

    if backup_path:
        console.print(f"[green]Backup created:[/green] [bold]{backup_path}[/bold]")
    else:
        console.print("[red]Backup failed.[/red] Check vault health or disk space.")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
