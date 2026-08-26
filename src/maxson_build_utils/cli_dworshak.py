# src/maxson_build_utils/cli_dworshak.py 
from __future__ import annotations

import shutil
import subprocess

import typer
from rich.console import Console

from .context import CONFIG_PATH, ENV_PATH, SECRET_PATH

console_stderr = Console(stderr=True)
"""
Aim to replace this with
```
from dworshak.typer import mount_dworshak
mount_dworshak(
    app,
    app_dir=APP_DIR,
    env_path=ENV_PATH,
)
```

much like add_typer_helptree()
"""
'''@app.command(
    name="dworshak",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def dworshak(ctx: typer.Context):
    """Run the Dworshak CLI using MBU's application config."""
    import shutil
    import subprocess

    args = list(ctx.args)

    # MBU owns all Dworshak storage paths. Do not permit callers
    # to override them through `mbu dworshak`.
    forbidden_options = {
        "-p",
        "--path",
        "-vp",
        "--vault-path",
    }

    if any(arg in forbidden_options for arg in args):
        console_stderr.print(
            "Error: path options are not available with `mbu dworshak`.",
            style="red",
        )
        raise typer.Exit(code=2)

    if not args:
        args = ["--help"]

    command = args[0]
    guard = len(args) >= 2

    if command == "config" and guard:
        args.extend(["-p", str(CONFIG_PATH)])

    elif command == "env" and guard:
        args.extend(["-p", str(ENV_PATH)])

    elif command == "secret" and guard:
        args.extend(["-vp", str(SECRET_PATH)])

    executable = shutil.which("dworshak")
    if executable is None:
        console_stderr.print(
            "[red]Dworshak CLI is required for `mbu dworshak`.[/red]"
        )
        console_stderr.print(
            '[yellow]Install it with:[/yellow] pipx install "dworshak[crypto], with the crypto extra if you plan to use encrypted secrets."'
        )
        raise typer.Exit(code=1)

    result = subprocess.run(
        [executable, *args],
    )

    raise typer.Exit(code=result.returncode)
'''

def dworshak_config(ctx: typer.Context):
    """Run the dworshak-config CLI using MBU's application config. This is carried as a dep."""
    import shutil
    import subprocess

    args = list(ctx.args)

    # MBU owns all Dworshak storage paths. Do not permit callers
    # to override them through `mbu dworshak-config`.
    forbidden_options = {
        "-p",
        "--path",
        "-vp",
        "--vault-path",
    }

    if any(arg in forbidden_options for arg in args):
        console_stderr.print(
            "Error: path options are not available with `mbu dworshak`.",
            style="red",
        )
        raise typer.Exit(code=2)

    if not args:
        args = ["--help"]

    guard = len(args) >= 1

    if guard:
        args.extend(["-p", str(CONFIG_PATH)])

    executable = shutil.which("dworshak-config")
    result = subprocess.run(
        [executable, *args],
    )

    raise typer.Exit(code=result.returncode)
