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
from .pyproject import get_toml_value

console = Console(stderr=True)

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


add_typer_helptree(app = app, console = console, version = __version__, hidden = False)


@app.command(name="vendor-wheels")
def vendor_wheels(
    dist_dir: Path = Path("dist"),
    vendor_dir: Path = Path("vendor-wheels")
):
    """Build project wheel and vendor offline dependencies, like when preparing for Flatpak."""
    run_vendor_wheels(dist_dir=dist_dir, vendor_dir=vendor_dir)


@app.command(name="build-deb")
def build_deb(
    app_name: str = typer.Option("cellshift", "--app-name", help="Package application name"),
    version: str = typer.Option("0.1.0", "--version", help="Version string"),
    arch: str = typer.Option("amd64", "--arch", help="Target architecture")
):
    """Assemble and build a Debian .deb package."""
    build_debian_package(app_name=app_name, version=version, arch=arch)


@app.command(name="build-appimage")
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
        Path.cwd() / "pyproject.toml",
        "--path",
        "-p",
        help="Path to pyproject.toml",
    ),
):
    """Extract project values using keys."""
    value = get_toml_value(*key, pyproject=path)

    if isinstance(value, (dict, list)):
        print(json.dumps(value, indent=2))
    else:
        print(value)

if __name__ == "__main__":
    app()
