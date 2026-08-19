#!/usr/bin/env python3
# src/maxson_build_utils/cli.py
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

from maxson_build_utils.deb import build_debian_package
from maxson_build_utils.vendor import run_vendor_wheels
from maxson_build_utils.linux_app_image import build_linux_appimage
from .pyproject import PyProject, format_value
from .scaffold import (
    run_init_changelog,
    run_init_gitignore,
    run_init_git,
    run_init_readme,
    run_init_src,
    run_init_gui,
    run_init_cli,
    run_init_context,
    run_init_config,
    run_init_core,
    run_init_helpers,
    run_init_pyproject,
    run_init_init,
    run_init_main,
    run_init_logging_setup,
    #run_init_webapp,
    # --- packaging ---
    run_init_icons,
    run_init_flatpak,
    run_init_appimage,
    # --- ci ---
    run_init_github_workflows,

)
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

build_app = typer.Typer(
    name="build",
    help="Run various builds. These rely on pre-existing manifest and spec files to be scaffolded.",
    no_args_is_help=True,
)

app.add_typer(build_app)

init_app = typer.Typer(
    name="init",
    help="Scaffold project files and directories.",
    no_args_is_help=True,
)

app.add_typer(init_app)

init_base_app = typer.Typer(
    name="base",
    help="Scaffold typical base files.",
    no_args_is_help=True,
)

init_app.add_typer(init_base_app)

init_src_app = typer.Typer(
    name="source",
    help="Scaffold typical source code files.",
    no_args_is_help=True,
)

init_app.add_typer(init_src_app)

init_pack_app = typer.Typer(
    name="packaging",
    help="Scaffold packaging assets (Flatpak, Debian, etc.).",
    no_args_is_help=True,
)

init_app.add_typer(init_pack_app)

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


@app.command(name="vendor-wheels")
def vendor_wheels(
    dist_dir: Path = Path("dist"),
    vendor_dir: Path = Path("vendor-wheels")
):
    """Build project wheel and vendor offline dependencies, like when preparing for Flatpak."""
    run_vendor_wheels(dist_dir=dist_dir, vendor_dir=vendor_dir)


@build_app.command(name="deb")
def build_deb(
    app_name: str = typer.Option(None, "--app-name", help="Package application name"),
    version: str = typer.Option(None, "--version", help="Version string"),
    arch: str = typer.Option(None, "--arch", help="Target architecture")
):
    """Assemble and build a Debian .deb package."""
    build_debian_package(app_name=app_name, version=version, arch=arch)


@build_app.command(name="appimage")
def build_appimage(
    app_pretty_name: str = typer.Option(..., "--pretty-name", help="Pretty desktop app display name"),
    icon: Path = typer.Option(..., "--icon", help="Path to source icon file, PNG preferred"),
    pyinstaller_onedir_exe_path: Path | None= typer.Option(None, "--exe-path", help="PyInstaller generated app filepath. Defaults to internal state.")        
):
    """Package a PyInstaller ONEDIR bundle into a standalone Linux AppImage. This must be run after the build_executable.py script for the application."""
    build_linux_appimage(
        app_name_pretty=app_pretty_name,
        icon_src=icon,
        app_filepath = pyinstaller_onedir_exe_path
    )

@app.command()
def pyproject(
    key: list[str] = typer.Option(
        ...,
        "--key",
        "-k",
        help="Nested TOML key. Repeat to traverse.",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to pyproject.toml",
    ),
):
    """Extract project values using keys."""
    #value = get_toml_value(*key, pyproject=path)
    pyproject = PyProject(path)
    value = pyproject.get(*key)
    if value is None:
        console_stderr.print(
            f"Key not found: {'.'.join(key)}",
            style="yellow",
        )
        raise typer.Exit(code=1)
    console_stdout.print(format_value(value))

# --- base scaffolding --- 

@init_base_app.command("pyproject")
def init_pyproject(
    overwrite: bool = typer.Option(
    False,
    "--overwrite",
    help="Allow overwriting an existing pyproject.toml.",
)
):
    """Generate or overwrite pyproject.toml in our own image."""
    path = run_init_pyproject(root_dir=None,overwrite=overwrite)
    console_stdout.print(f"{path}")

@init_base_app.command("changelog")
def init_changelog():
    """Create docs/CHANGELOG.md."""
    path = run_init_changelog()
    console_stdout.print(f"{path}")

@init_base_app.command("readme")
def init_readme():
    """Create README.md."""
    path = run_init_readme()
    console_stdout.print(f"{path}")

@init_base_app.command("git")
def init_git():
    """Create .git."""
    path = run_init_git()
    console_stdout.print(f"{path}")

@init_base_app.command("gitignore")
def init_gitignore():
    """Create .gitignore."""
    path = run_init_gitignore()
    console_stdout.print(f"{path}")

# --- source code scaffolding ---
@init_src_app.command("src")
def init_src():
    """Build src/<app_name>/ with automatic snake case."""
    path = run_init_src()
    console_stdout.print(f"{path}")

@init_src_app.command("gui")
def init_gui():
    """Create src/<app>/gui.py."""
    path = run_init_gui()
    console_stdout.print(f"{path}")

@init_src_app.command("cli")
def init_cli():
    """Create src/<app>/cli.py."""
    path = run_init_cli()
    console_stdout.print(f"{path}")

@init_src_app.command("core")
def init_core():
    """Create src/<app>/core.py."""
    path = run_init_core()
    console_stdout.print(f"{path}")

@init_src_app.command("__init__")
def init_init(
    overwrite: bool = typer.Option(
    False,
    "--overwrite",
    help="Allow overwriting an existing file.",
)
):
    """Create src/<app>/__init__.py"""
    path = run_init_init(root_dir=None,overwrite=overwrite)
    console_stdout.print(f"{path}")

@init_src_app.command("__main__")
def init_main(
    overwrite: bool = typer.Option(
    False,
    "--overwrite",
    help="Allow overwriting an existing file.",
)
):
    """Create src/<app>/__main__.py"""
    path = run_init_main(root_dir=None,overwrite=overwrite)
    console_stdout.print(f"{path}")


'''@init_src_app.command("webapp")
def init_webapp():
    """Create src/<app>/webapp.py."""
    path = run_init_webapp()
    console_stdout.print(f"{path}")
'''

@init_src_app.command("context")
def init_context():
    """Create src/<app>/context.py."""
    path = run_init_context()
    console_stdout.print(f"{path}")

@init_src_app.command("config")
def init_config():
    """Create src/<app>/config.py."""
    path = run_init_config()
    console_stdout.print(f"{path}")

@init_src_app.command("logging_setup")
def init_logging_setup():
    """Create src/<app>/logging_setup.py."""
    path = run_init_logging_setup()
    console_stdout.print(f"{path}")

# --- packaging scaffolding ---

@init_pack_app.command("icons")
def init_icons():
    """Copy the stock Maxson icons into the project's data/icons directory."""
    path = run_init_icons()
    console_stdout.print(f"{path}")

@init_pack_app.command("flatpak")
def init_pack_flatpak():
    """Scaffold packaging/flatpak/ metadata and manifests."""
    paths = run_init_flatpak()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("pyinstaller")
def init_pack_pyinstaller():
    """Scaffold packaging/pyinstaller/build_executable.py metadata and manifests."""
    paths = run_init_pyinstaller()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("shiv")
def init_pack_shiv():
    """Scaffold packaging/shiv/build_pyz.py metadata and manifests."""
    paths = run_init_shiv()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("msix")
def init_pack_msix():
    """Scaffold packaging/msix/msix.py metadata and manifests."""
    paths = run_init_msix()
    for path in paths:
        console_stdout.print(f"{path}")


@init_pack_app.command("deb")
def init_pack_deb():
    """Scaffold packaging/deb/deb.py metadata and manifests."""
    paths = run_init_deb()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("dmg")
def init_pack_dmg():
    """Scaffold packaging/macos/dmg.py metadata and manifests."""
    paths = run_init_dmg()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("appimage")
def init_pack_appimage():
    """Scaffold packaging/appimage/ metadata and manifests."""
    paths = run_init_appimage()
    for path in paths:
        console_stdout.print(f"{path}")

@init_pack_app.command("all")
def init_pack_all():
    """Create all packaging scaffolding."""
    init_pack_deb()
    init_pack_dmg()
    init_pack_msix()
    init_pack_shiv()
    init_pack_pyinstaller()
    init_pack_flatpak()
    init_pack_appimage()


@init_app.command("all")
def init_all():
    """Run all project scaffolding steps."""
    # Execute source code files + packaging
    # --- source code ---
    run_init_pyproject()
    run_init_git()
    run_init_gitignore()
    run_init_readme()
    run_init_changelog()
    run_init_src()
    run_init_main()
    run_init_init()
    run_init_context()
    run_init_config()
    run_init_core()
    run_init_helpers()
    run_init_cli()
    run_init_gui()
    run_init_logging_setup()
    # --- packaging ---
    run_init_icons()
    run_init_flatpak()
    # --- ci ---
    run_init_github_workflows()

    console_stdout.print("Successfully initialized all project scaffolds.")

if __name__ == "__main__":
    app()
