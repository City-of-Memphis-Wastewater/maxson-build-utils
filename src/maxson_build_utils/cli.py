#!/usr/bin/env python3
# src/maxson_build_utils/cli.py
import os
import sys
import typer
from pathlib import Path
from typer_helptree import add_typer_helptree
from rich.console import Console
import subprocess

from maxson_build_utils import __version__
from maxson_build_utils.logging_setup import (
    configure_logging_all_debug,
    configure_logging_for_application,
    get_logger,
)

logger = get_logger(__name__)

from .context import DESCRIPTION_STR, APP_NAME
from .helpers import print_write_results
from ._version import __version__

from maxson_build_utils import MaxsonPyProject
from maxson_build_utils.builders.pyinstaller import run_build_executable
from maxson_build_utils.builders.shiv import run_build_pyz
from maxson_build_utils.helpers import PyinsMode
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
    run_init_version,
    run_init_version_num,
    run_init_logging_setup,
    #run_init_webapp,
)
from .scaffold.ci import (
    # --- ci ---
    run_init_github_ci,
)
from .scaffold.packaging import (
    # --- packaging ---
    run_init_icons,
    run_init_flatpak,
    run_init_appimage,
    run_init_deb,
    run_init_msix,
    run_init_dmg,
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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show application version and exit."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug level logs for app."),
    all_debug: bool = typer.Option(False, "--all-debug", help="Enable debug logs for app AND dependencies."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose info level logs."),
    log_file: Path | None = typer.Option(None, "--log-file", help="Custom path to output log file."),
):
    if version:
        typer.echo(__version__)
        raise typer.Exit()

    # Route logging configuration based on CLI options
    if all_debug:
        configure_logging_all_debug()
    else:
        configure_logging_for_application(
            debug=debug,
            verbose=verbose,
            log_to_file=log_file is not None,
        )

    # Log invoked CLI command invocation string neatly
    logger.debug("Executing command: %s", " ".join(sys.argv))

    # Fallback to showing help if invoker passed no commands
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    
# ----

add_typer_helptree(app = app, console = console_stderr, version = __version__, hidden = False)

# --- sub apps ---

dworshak_app = typer.Typer(
    name="dworshak",
    help ="dworshak CLI with path resolved to this app.",
    no_args_is_help=True,
)

app.add_typer(dworshak_app)

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

init_ci_app = typer.Typer(
    name="ci",
    help="Scaffold ci assets (github runners).",
    no_args_is_help=True,
)

init_app.add_typer(init_ci_app)

# ---

@app.command(name="vendor-wheels")
def vendor_wheels(
    dist_dir: Path = Path("dist"),
    vendor_dir: Path = Path("vendor-wheels")
):
    """Build project wheel and vendor offline dependencies, like when preparing for Flatpak."""
    run_vendor_wheels(dist_dir=dist_dir, vendor_dir=vendor_dir)


@build_app.command(name="pyinstaller")
def build_pyinstaller(
    mode: PyinsMode = typer.Option(
        PyinsMode.ONEDIR,
        "--mode",
        "-m",
        help="Build mode: 'onedir' (default for downstream pipelines) or 'onefile'.",
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Override target app version string. Defaults to src/<app>/VERSION file.",
    ),
    windowed: bool | None = typer.Option(
        None,
        "--windowed/--console",
        help="Force windowed (GUI) or console mode. Overrides pyproject settings.",
    ),
    collect_data: list[str] = typer.Option(
        [],
        "--collect-data",
        "-d",
        help="Packages to collect data files from (can be passed multiple times).",
    ),
    collect_binary: list[str] = typer.Option(
        [],
        "--collect-binary",
        "-b",
        help="Packages to collect binary files from (can be passed multiple times).",
    ),
):
    """Build PyInstaller binary using pyproject.toml configuration and CLI overrides."""
    pyproject = MaxsonPyProject()

    # Resolve target version: CLI parameter -> src/<app>/VERSION -> fallback
    target_version = version or pyproject.version
    
    # Read [tool.mbu.pyinstaller] table from pyproject.toml if present
    mbu_config = pyproject.get("tool", "maxson-build-utils", "pyinstaller") or {}
    
    # Resolve parameters: CLI arguments take precedence over pyproject.toml
    final_mode = mode or PyinsMode(mbu_config.get("mode", "onedir"))
    final_windowed = windowed if windowed is not None else mbu_config.get("windowed", None)
    
    # Merge CLI collect flags with TOML configuration sets
    config_data_pkgs = set(mbu_config.get("collect_data_pkgs", []))
    final_collect_data = list(config_data_pkgs.union(collect_data)) or [pyproject.import_name]
    
    config_binary_pkgs = set(mbu_config.get("collect_binary_pkgs", []))
    final_collect_binary = list(config_binary_pkgs.union(collect_binary))

    typer.secho(
        f"Building '{pyproject.import_name}' v{target_version} ({final_mode.value}) via PyInstaller...",
        fg=typer.colors.CYAN,
    )

    app_filepath, _ = run_build_executable(
        src_folder_name=pyproject.import_name,
        version=target_version,
        mode=final_mode,
        is_windowed_build=final_windowed,
        collect_data_pkgs=final_collect_data,
        collect_binary_pkgs=final_collect_binary,
    )

    typer.secho(f"Successfully built binary to: {app_filepath}", fg=typer.colors.GREEN)

@build_app.command(name="shiv")
def build_pyz(
    version: str = typer.Option(None, "--version", help="Version string"),
):
    """Assemble and build a Shiv .pyz package."""
    run_build_pyz()

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
def init_pyproject(overwrite: bool = typer.Option(False, "--overwrite", "-o")):
    """Generate or overwrite pyproject.toml in our own image."""
    # Ensure root_dir resolves to current working directory if not explicitly provided
    run_init_pyproject(root_dir=Path.cwd(), overwrite=overwrite).print_path(console_stdout)

@init_base_app.command("changelog")
def init_changelog():
    """Create docs/CHANGELOG.md."""
    run_init_changelog().print_path(console_stdout)

@init_base_app.command("readme")
def init_readme():
    """Create README.md."""
    run_init_readme().print_path(console_stdout)

@init_base_app.command("git")
def init_git():
    """Create .git."""
    path = run_init_git()
    console_stdout.print(path)

@init_base_app.command("gitignore")
def init_gitignore():
    """Create .gitignore."""
    run_init_gitignore().print_path(console_stdout)

# --- source code scaffolding ---
@init_src_app.command("src")
def init_src():
    """Build src/<app_name>/ with automatic snake case."""
    path = run_init_src()
    console_stdout.print(path)

@init_src_app.command("gui")
def init_gui():
    """Create src/<app>/gui.py."""
    run_init_gui().print_path(console_stdout)

@init_src_app.command("cli")
def init_cli():
    """Create src/<app>/cli.py."""
    run_init_cli().print_path(console_stdout)

@init_src_app.command("core")
def init_core():
    """Create src/<app>/core.py."""
    run_init_core().print_path(console_stdout)

@init_src_app.command("__init__")
def init_init(
    overwrite: bool = typer.Option(
    False,
    "--overwrite",
    help="Allow overwriting an existing file.",
)
):
    """Create src/<app>/__init__.py"""
    run_init_init(root_dir=None,overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("__main__")
def init_main(
    overwrite: bool = typer.Option(
    False,
    "--overwrite",
    help="Allow overwriting an existing file.",
)
):
    """Create src/<app>/__main__.py"""
    run_init_main(root_dir=None,overwrite=overwrite).print_path(console_stdout)


'''@init_src_app.command("webapp")
def init_webapp():
    """Create src/<app>/webapp.py."""
    run_init_webapp().print_path(console_stdout)
'''

@init_src_app.command("context")
def init_context():
    """Create src/<app>/context.py."""
    run_init_context().print_path(console_stdout)

@init_src_app.command("version")
def init_version():
    """Create src/<app>/_version.py and src/<app>/VERSION."""
    run_init_version().print_path(console_stdout)
    run_init_version_num().print_path(console_stdout)

@init_src_app.command("config")
def init_config():
    """Create src/<app>/config.py."""
    run_init_config().print_path(console_stdout)

@init_src_app.command("helpers")
def init_helpers():
    """Create src/<app>/helpers.py."""
    run_init_helpers().print_path(console_stdout)

@init_src_app.command("logging_setup")
def init_logging_setup():
    """Create src/<app>/logging_setup.py."""
    run_init_logging_setup().print_path(console_stdout)

# --- packaging scaffolding ---

@init_pack_app.command("icons")
def init_icons():
    """Copy the stock Maxson icons into the project's data/icons directory."""
    print_write_results(run_init_icons(),console_stdout)

@init_pack_app.command("flatpak")
def init_pack_flatpak():
    """Scaffold packaging/flatpak/ metadata and manifests."""
    print_write_results(run_init_flatpak(),console_stdout)

@init_pack_app.command("shiv")
def init_pack_shiv():
    """Scaffold packaging/shiv/build_pyz.py metadata and manifests."""
    print_write_results(run_init_shiv(),console_stdout)

@init_pack_app.command("msix")
def init_pack_msix():
    """Scaffold packaging/msix/msix.py metadata and manifests."""
    print_write_results(run_init_msix(),console_stdout)

@init_pack_app.command("deb")
def init_pack_deb():
    """Scaffold packaging/deb/deb.py metadata and manifests."""
    print_write_results(run_init_deb(),console_stdout)

@init_pack_app.command("dmg")
def init_pack_dmg():
    """Scaffold packaging/macos/dmg.py metadata and manifests."""
    print_write_results(run_init_dmg(),console_stdout)

@init_pack_app.command("appimage")
def init_pack_appimage():
    """Scaffold packaging/appimage/ metadata and manifests."""
    print_write_results(run_init_appimage(),console_stdout)

# ---

@init_ci_app.command("github")
def init_github_ci():
    """Scaffold github workers"""
    print_write_results(run_init_github_ci(),console_stdout)

# ---

@init_base_app.command("all")
def init_base_all():
    init_pyproject()
    init_git()
    init_gitignore()
    init_readme()
    init_changelog()

@init_src_app.command("all")
def init_source_all():
    init_src()
    init_main()
    init_init()
    init_context()
    init_config()
    init_core()
    init_helpers()
    init_version()
    init_cli()
    init_gui()
    init_logging_setup()

@init_pack_app.command("all")
def init_pack_all():
    """Create all packaging scaffolding."""
    init_pack_deb()
    init_pack_dmg()
    init_pack_msix()
    #init_pack_shiv()
    init_pack_flatpak()
    init_pack_appimage()

@init_ci_app.command("all")
def init_ci_all():
    """Create all ci scaffolding."""
    init_github_ci()

@init_app.command("all")
def init_all():
    """Run all project scaffolding steps."""
    init_base_all()
    init_source_all()
    init_pack_all()
    init_ci_all()

    console_stdout.print("Successfully initialized all project scaffolds.")

if __name__ == "__main__":
    app()
