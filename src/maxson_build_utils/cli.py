#!/usr/bin/env python3
# src/maxson_build_utils/cli.py
import os
import sys
import pyhabitat
from pyhabitat import probe_app_mode_mgu, AppMode
import typer
from typer.models import OptionInfo
from pathlib import Path
from typer_helptree import add_typer_helptree
#from rich.console import Console
from blindwindow.core import (
    Console,
    get_spool_path,
    install_stream_wrappers,
)
from maxson_build_utils.logging_setup import (
    configure_logging_all_debug,
    configure_logging_for_application,
    get_logger,
)

logger = get_logger(__name__)

from .context import DESCRIPTION_STR, APP_NAME, APP_DIR, CONFIG_PATH, ENV_PATH, SECRET_PATH, APP_NAME_PRETTY
from .helpers import (print_write_results, PyinsMode, form_dynamic_name)
from .gui_multiplex import GuiInterface
from ._version import __version__

from .cli_dworshak import dworshak_config as run_dworshak_config
from maxson_build_utils.pyproject import MaxsonPyProject

from maxson_build_utils.builders import (
    TargetBuild,
    validate_build_target, 
    run_build_executable,
    run_build_pyz,
    build_macos_dmg,
    build_debian_package,
    build_linux_appimage,
    build_msix,
    build_flatpak,
    build_buildozer,
    BuildozerMode,
)
from maxson_build_utils.builders.pyinstaller import run_build_from_spec

from maxson_build_utils.helpers import PyinsMode
from maxson_build_utils.vendor import run_vendor_wheels, run_vendor_site_packages, VENDOR_SITE_PACKAGES_DIR, VENDOR_WHEELS_DIR, DIST_WHEELS_DIR, DEFAULT_EXTRA_ARGS
from .pyproject import PyProject, format_value
from .scaffold.base import (
    run_init_pyproject,
    run_init_changelog,
    run_init_gitignore,
    run_init_git,
    run_init_readme,
    run_init_manifest,
)
from .scaffold.source import (
    run_init_tk_gui,
    run_init_cli,
    run_init_context,
    run_init_config,
    run_init_core,
    run_init_helpers,
    run_init_init,
    run_init_main,
    run_init_version,
    run_init_version_num,
    run_init_logging_setup,
    #run_init_webapp,
    run_init_kivy,
    run_init_buildozer_source_entry,
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
    run_init_buildozer_spec,
    run_init_pyinstaller_spec,
)
'''
from .signers import (
    sign_dmg,
    sign_msix
)
'''
#console_stderr = Console(stderr=True)
#console_stdout = Console()
console_stderr = Console(stderr=True, tee_sys=True) # tee_sys arg is particular to blindwindow and will fail for rich.console.Console()
console_stdout = Console(stderr=False, tee_sys=True) # tee_sys arg is particular to blindwindow

# Force Rich to always enable colors, even when running from a .pyz bundle
os.environ["FORCE_COLOR"] = "1"
# Optional but helpful for full terminal feature detection
os.environ["TERM"] = "xterm-256color"

try:
    # Capture process-level prints & Typer help screens
    install_stream_wrappers() # defaults to same path as get_spool_path()
    logger.debug("[CLI] Installed stream wrappers targeting default spool: %s", get_spool_path())
except:
    print("blindwindow failed to install stream wrappers.")

app_mode = probe_app_mode_mgu()

app = typer.Typer(
    name=APP_NAME,
    help=f"{DESCRIPTION_STR} (v{__version__})",
    add_completion=False,
    invoke_without_command = True,
    no_args_is_help = (app_mode == AppMode.TYPER_CLI),
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
    log_file: Path | None = typer.Option(None, "--log-file", help="Custom path to output log file."), # path just goes unused, just converted to bool
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

    if ctx.invoked_subcommand is None:
        if app_mode == AppMode.TK_GUI:
            from .tk_gui import start_gui
            start_gui()
        else:
            typer.echo(ctx.get_help())
            raise typer.Exit()

# ----

add_typer_helptree(app = app, console = console_stderr, version = __version__, hidden = False)

# --- sub apps ---

vendor_app = typer.Typer(
    name="vendor",
    help="Vendor dependencies for local builds. Thin wrapper around 'uv pip' with opinionated target directories.",
    no_args_is_help=True,
)

app.add_typer(vendor_app)

build_app = typer.Typer(
    name="build",
    help="Run various builds. These rely on pre-existing manifest and spec files to be scaffolded.",
    no_args_is_help=True,
)

app.add_typer(build_app)

'''
sign_app = typer.Typer(
    name="sign",
    help="Sign MSIX and DMG (and AppImage?). This requires a pyinstaller onedir process, then the MSIX and DMG build process, and only when those assets are avaible to the current environment in the expected relative paths will the signing work. Alteratively, just put the signing in the YML GitHub Workflow Runner, say in './.github/workflows/reusable-dmg.yml'.",
    no_args_is_help=True,
)

app.add_typer(sign_app)
'''

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

@vendor_app.command(name="wheels")
def vendor_wheels_cmd(
    dist_dir: Path = DIST_WHEELS_DIR,
    vendor_dir: Path = VENDOR_WHEELS_DIR,
):
    """Build project wheel and vendor offline dependencies, like when preparing for Flatpak."""
    run_vendor_wheels(dist_dir=dist_dir, vendor_dir=vendor_dir)


@vendor_app.command(name="site-packages")
def vendor_site_packages_cmd(
    vendor_dir: Path = VENDOR_SITE_PACKAGES_DIR,
    extra_args: list[str] = typer.Option(
        DEFAULT_EXTRA_ARGS,
        "--extra-args",
        "-e",
        help="Extra arguments passed directly to 'uv pip install'.",
    ),
    reinstall: bool = typer.Option(
        False, "--reinstall", help="Force re-installation of all packages."
    ),
):
    """Build project packages and .dist-info offline, like when preparing for buildozer."""
    run_vendor_site_packages(
        vendor_dir=vendor_dir, extra_args=extra_args, reinstall=reinstall
    )

# ---

@app.command(
    name="dworshak-config",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def dworshak_config(ctx: typer.Context):
    """Run the dworshak-config CLI using MBU's application config. This is carried as a dep."""
    run_dworshak_config(ctx)


# ---

@build_app.command(name="pyinstaller-from-spec")
def build_pyinstaller_from_spec_command(
    spec_path: Path = typer.Option(
        None,
        "--spec",
        "-s",
        help="Custom path to the PyInstaller .spec file. Defaults to packaging/pyinstaller/<import_name>.spec",
    ),
    mode: PyinsMode = typer.Option(
        PyinsMode.ONEDIR,
        "--mode",
        "-m",
        help="Build mode: 'onedir' or 'onefile'.",
    ),
    windowed: bool = typer.Option(
        False,
        "--windowed",
        "-w",
        help="Target windowed GUI build rather than console.",
    ),
) -> None:
    """Build a PyInstaller artifact using a native spec file."""
    pyproject = MaxsonPyProject()
    
    # 1. Resolve spec path
    if spec_path is None:
        spec_path = Path.cwd() / "packaging" / "pyinstaller" / f"{pyproject.import_name}.spec"

    if not spec_path.exists():
        typer.secho(
            f"Error: Spec file not found at {spec_path}. Run 'mbu init pyinstaller-spec' first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # 2. Determine descriptor name
    version = pyproject.version or "0.1.0"
    executable_descriptor = form_dynamic_name(
        pkg_name=pyproject.import_name,
        version=version,
        mode=mode,
    )

    typer.secho(
        f"Building PyInstaller artifact from spec: {spec_path}",
        fg=typer.colors.CYAN,
    )

    # 3. Trigger spec builder
    app_filepath, app_filename = run_build_from_spec(
        spec_path=spec_path,
        executable_descriptor=executable_descriptor,
        mode=mode,
        is_windowed=windowed,
    )

    typer.secho(
        f"Successfully built spec artifact: {app_filepath}",
        fg=typer.colors.GREEN,
    )
    
# ---
@build_app.command(name="pyinstaller")
def build_pyinstaller(
    mode: PyinsMode = typer.Option(
        PyinsMode.ONEDIR,
        "--mode",
        "-m",
        help="Build mode: 'onedir' (default for downstream pipelines) or 'onefile'.",
    ),
    gui_interface: GuiInterface = typer.Option(
        GuiInterface.TK,
        "--gui-interface",
        "-g",
        help = "Decide which interface entry point to include in pyinstaller build"
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
    test_gui: bool = typer.Option(
    False,
    "--test-gui",
    help="Test the GUI launch for the generated PYZ.",
    )
):
    """Assemble and build a Shiv .pyz package."""
    run_build_pyz(version=version,test_gui=test_gui)

@build_app.command(name="deb")
def build_deb(
    app_name: str = typer.Option(None, "--app-name", help="Package application name"),
    version: str = typer.Option(None, "--version", help="Version string"),
    arch: str = typer.Option(None, "--arch", help="Target architecture")
):
    """Package a PyInstaller ONEDIR bundle into a standalone Debian .deb file. This must be run after pyinstaller onedir."""
    validate_build_target(TargetBuild.DEB)

    build_debian_package(app_name=app_name, version=version, arch=arch)


@build_app.command(name="appimage")
def build_appimage_command(
    app_pretty_name: str | None= typer.Option(None, "--pretty-name", help="Pretty desktop app display name"),
    icon: Path = typer.Option(None, "--icon", help="Path to source icon file, PNG preferred"),
    pyinstaller_onedir_export_entrypoint_path: Path | None= typer.Option(None, "--exe-path", help="PyInstaller generated app filepath. Defaults to internal state.")        
):
    """Package a PyInstaller ONEDIR bundle into a standalone Linux AppImage. This must be run after pyinstaller onedir."""
    validate_build_target(TargetBuild.APPIMAGE)
    if app_pretty_name is None:
        proj=MaxsonPyProject()
        app_pretty_name = proj.pretty_name
    
    build_linux_appimage(
        app_name_pretty=app_pretty_name,
        icon_src=icon,
        app_filepath = pyinstaller_onedir_export_entrypoint_path
    )

@build_app.command(name="dmg")
def build_macos_dmg_command(
    app_pretty_name: str | None = typer.Option(None, "--pretty-name", help="Pretty desktop app display name"),
    pyinstaller_onedir_export_entrypoint_path: Path | None= typer.Option(None, "--exe-path", help="PyInstaller generated app filepath. Defaults to internal state."),
    version: str | None = typer.Option(
            None,
            "--version",
            "-v",
            help="Override target app version string. Defaults to src/<app>/VERSION file.",
        ),
):
    """Package a PyInstaller ONEDIR .app export into a MacOS DMG."""
    validate_build_target(TargetBuild.DMG)

    app_pretty_name = app_pretty_name if app_pretty_name is not None else None
    version = version if version is not None else None

    build_macos_dmg(
        app=pyinstaller_onedir_export_entrypoint_path,
        app_pretty_name=app_pretty_name,
        version=version,
    )

@build_app.command(name="flatpak")
def build_flatpak_cmd():
    """Build a standalone Flatpak single-file bundle (.flatpak)."""
    build_flatpak()

@build_app.command("msix")
def build_msix_command():
    """Package a PyInstaller ONEDIR bundle into a Windows MSIX."""
    build_msix()

@build_app.command(name="buildozer")
def build_buildozer_command(
    mode: BuildozerMode = typer.Option(
        BuildozerMode.APK,
        "--mode",
        "-m",
        help="Build type: 'apk' for debug APK or 'aab' for release Android App Bundle.",
    ),
    check_vendor: bool = typer.Option(
        True,
        "--check-vendor/--no-check-vendor",
        help="Perform pre-flight check to ensure vendor/site-packages is populated.",
    ),
    vendor_dir: Path | None = typer.Option(
        VENDOR_SITE_PACKAGES_DIR,
        "--vendor-dir",
        "-v",
        help="Custom path to vendored site-packages directory.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        show_default=True,
    ),
):
    """Build an Android application with Buildozer."""

    typer.secho(
        f"Building Android {mode.value} with Buildozer...",
        fg=typer.colors.CYAN,
    )

    output_dir = build_buildozer(
            mode=mode,
            check_vendor=check_vendor,
            vendor_dir=vendor_dir,
        )
    typer.secho(
        f"Build completed in: {output_dir}",
        fg=typer.colors.GREEN,
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

# -----------------------------------------------


# --- base scaffolding --- 

@init_base_app.command("pyproject")
def init_pyproject(overwrite: bool = typer.Option(False, "--overwrite", "-o", help="Allow overwriting existing file.")):
    """Generate or overwrite pyproject.toml in our own image."""
    run_init_pyproject(root_dir=Path.cwd(), overwrite=overwrite).print_path(console_stdout)

@init_base_app.command("changelog")
def init_changelog(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create docs/CHANGELOG.md."""
    run_init_changelog(overwrite=overwrite).print_path(console_stdout)

@init_base_app.command("readme")
def init_readme(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create README.md."""
    run_init_readme(overwrite=overwrite).print_path(console_stdout)

@init_base_app.command("manifest")
def init_manifest(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create MANIFEST.in."""
    run_init_manifest(overwrite=overwrite).print_path(console_stdout)

@init_base_app.command("git")
def init_git():
    """Create .git."""
    path = run_init_git()
    console_stdout.print(path)

@init_base_app.command("gitignore")
def init_gitignore(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create .gitignore."""
    run_init_gitignore(overwrite=overwrite).print_path(console_stdout)


# --- source code scaffolding ---

@init_src_app.command("cli")
def init_cli(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/cli.py."""
    run_init_cli(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("core")
def init_core(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/core.py."""
    run_init_core(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("__init__")
def init_init(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting an existing file.")):
    """Create src/<app>/__init__.py"""
    run_init_init(root_dir=None, overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("__main__")
def init_main(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting an existing file.")):
    """Create src/<app>/__main__.py"""
    run_init_main(root_dir=None, overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("context")
def init_context(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/context.py."""
    run_init_context(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("version")
def init_version(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Create src/<app>/_version.py and src/<app>/VERSION."""
    run_init_version(overwrite=overwrite).print_path(console_stdout)
    run_init_version_num(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("config")
def init_config(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/config.py."""
    run_init_config(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("helpers")
def init_helpers(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/helpers.py."""
    run_init_helpers(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("logging_setup")
def init_logging_setup(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create src/<app>/logging_setup.py."""
    run_init_logging_setup(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("kivy-gui")
def init_kivy_gui(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Create files in src/<app>/kivy/ dir, including app.py."""
    print_write_results(run_init_kivy(overwrite=overwrite), console_stdout)

@init_src_app.command("tk-gui")
def init_tk_gui(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing file.")):
    """Create file at src/<app>/tk_gui.py"""
    run_init_tk_gui(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("buildozer")
def init_buildozer_entry(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Create src/SOURCE_NAME/__buildozer_entry__.py. and main.py shim"""
    print_write_results(run_init_buildozer_source_entry(overwrite=overwrite), console_stdout)

# --- packaging scaffolding ---

@init_pack_app.command("icons")
def init_icons(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Copy the stock Maxson icons into the project's data/icons directory."""
    print_write_results(run_init_icons(overwrite=overwrite), console_stdout)

@init_pack_app.command("flatpak")
def init_pack_flatpak(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/flatpak/ metadata and manifests."""
    print_write_results(run_init_flatpak(overwrite=overwrite), console_stdout)

@init_pack_app.command("buildozer")
def init_pack_buildozer(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/buildozer/ spec file."""
    print_write_results(run_init_buildozer_spec(overwrite=overwrite), console_stdout)

@init_pack_app.command("pyinstaller")
def init_pack_pyinstaller(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/pyinstaller/ spec file(s)."""
    print_write_results(run_init_pyinstaller_spec(overwrite=overwrite), console_stdout)

@init_pack_app.command("msix")
def init_pack_msix(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/msix/msix.py metadata and manifests."""
    print_write_results(run_init_msix(overwrite=overwrite), console_stdout)

@init_pack_app.command("deb")
def init_pack_deb(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/deb/deb.py metadata and manifests."""
    print_write_results(run_init_deb(overwrite=overwrite), console_stdout)

@init_pack_app.command("dmg")
def init_pack_dmg(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/macos/dmg.py metadata and manifests."""
    print_write_results(run_init_dmg(overwrite=overwrite), console_stdout)

@init_pack_app.command("appimage")
def init_pack_appimage(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold packaging/appimage/ metadata and manifests."""
    print_write_results(run_init_appimage(overwrite=overwrite), console_stdout)


# --- CI scaffolding ---

@init_ci_app.command("github")
def init_github_ci(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files.")):
    """Scaffold github workers"""
    print_write_results(run_init_github_ci(overwrite=overwrite), console_stdout)


# --- Aggregation Group Handlers (No wrappers called directly) ---

@init_base_app.command("all")
def init_base_all(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files across base modules.")):
    """Create all base scaffolding."""
    run_init_pyproject(root_dir=Path.cwd(), overwrite=overwrite).print_path(console_stdout)
    run_init_git()
    run_init_gitignore(overwrite=overwrite).print_path(console_stdout)
    run_init_readme(overwrite=overwrite).print_path(console_stdout)
    run_init_changelog(overwrite=overwrite).print_path(console_stdout)
    run_init_manifest(overwrite=overwrite).print_path(console_stdout)

@init_src_app.command("all")
def init_source_all(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files across source modules.")):
    """Create all source code scaffolding."""
    run_init_main(root_dir=None, overwrite=overwrite).print_path(console_stdout)
    run_init_init(root_dir=None, overwrite=overwrite).print_path(console_stdout)
    run_init_context(overwrite=overwrite).print_path(console_stdout)
    run_init_config(overwrite=overwrite).print_path(console_stdout)
    run_init_logging_setup(overwrite=overwrite).print_path(console_stdout)
    run_init_helpers(overwrite=overwrite).print_path(console_stdout)
    run_init_version(overwrite=overwrite).print_path(console_stdout) 
    run_init_version_num(overwrite=overwrite).print_path(console_stdout)
    run_init_cli(overwrite=overwrite).print_path(console_stdout)
    run_init_tk_gui(overwrite=overwrite).print_path(console_stdout)
    print_write_results(run_init_kivy(overwrite=overwrite), console_stdout)
    print_write_results(run_init_buildozer_source_entry(overwrite=overwrite), console_stdout)
    run_init_core(overwrite=overwrite).print_path(console_stdout)

@init_pack_app.command("all")
def init_pack_all(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files across packaging assets.")):
    """Create all packaging scaffolding."""
    print_write_results(run_init_deb(overwrite=overwrite), console_stdout)
    print_write_results(run_init_dmg(overwrite=overwrite), console_stdout)
    print_write_results(run_init_msix(overwrite=overwrite), console_stdout)
    print_write_results(run_init_flatpak(overwrite=overwrite), console_stdout)
    print_write_results(run_init_appimage(overwrite=overwrite), console_stdout)
    print_write_results(run_init_buildozer_spec(overwrite=overwrite), console_stdout)
    print_write_results(run_init_pyinstaller_spec(overwrite=overwrite), console_stdout)
    print_write_results(run_init_icons(overwrite=overwrite), console_stdout)

@init_ci_app.command("all")
def init_ci_all(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files across CI workflows.")):
    """Create all ci scaffolding."""
    print_write_results(run_init_github_ci(overwrite=overwrite), console_stdout)

@init_app.command("all")
def init_all(overwrite: bool = typer.Option(False, "--overwrite", help="Allow overwriting existing files across all modules.")):
    """Run all project scaffolding steps."""
    init_base_all(overwrite=overwrite)
    init_source_all(overwrite=overwrite)
    init_pack_all(overwrite=overwrite)
    init_ci_all(overwrite=overwrite)


# -----

@app.command(name="gui")
def gui_command(
    auto_close: int = typer.Option(0,
   "--auto-close", "-c",
   help = "Delay in milliseconds after which the GUI window will close (for automated testing). Use 0 to disable auto-closing.",
   min=0)
    )->None:
    """
    Launch tkinter-based GUI.
    """
    assured_auto_close_value = 0

    # --- Helper, consistent gui failure message. ---
    def _gui_failure_msg():
        console_stderr.print("[bold red]GUI failed to launch[/bold red]")
        console_stderr.print("Use CLI instead.")
        console_stderr.print(f"pyhabitat.tkinter_is_available() = {pyhabitat.tkinter_is_available()}")
        console_stderr.print(f"pyhabitat.on_termux() = {pyhabitat.on_termux()}")

    if isinstance(auto_close, OptionInfo):
        # Case 1: Called implicitly from main() (with no args)
        # We received the metadata object, so use the function's default value (0).
        # We don't need to do anything here since final_auto_close_value is already 0.
        pass
    else:
        # Case 2: Called explicitly by Typer (gui -c 3000)
        # Typer has successfully converted the command line argument, and auto_close is an int.
        assured_auto_close_value = int(auto_close)

    if not pyhabitat.tkinter_is_available():
        _gui_failure_msg()
        return

    from .tk_gui import start_gui
    start_gui(time_auto_close = assured_auto_close_value)

@app.command(name="serve")
def serve_webapp_command(
   #auto_close: int = typer.Option(0,
   #"--auto-close", "-c",
   #help = "Delay in milliseconds after which the GUI window will close (for automated testing). Use 0 to disable auto-closing.",
   #min=0)
   )->None:
   """Serve webapp on this system."""
   console_stdout.print("None")

'''
@sign_app.command(name="msix")
def sign_msix_command():
    """Sign MSIX files for Windows distribution."""
    sign_msix()

@sign_app.command(name="dmg")
def sign_dmg_command(
    p12_file: str=typer.Option(None,
        '--p12-file',help = "Base 64 .p12 file"
    ),
    p12_password: str=typer.Option(None,
        '--p12-password',help = "secret"
    ),
    path: str|None=typer.Option(None,
        '--path',help = "paths/to/assets"
    )
):
    """A wrapper around rcodesign. Sign DMG file for macOS, assuming create-dmg has already been run."""
    
    if path is None:
        dmg_files = list((Path.cwd() / "dist" / "dmg").glob("*.dmg"))

        if not dmg_files:
            raise FileNotFoundError(
                f"No DMG files found in {Path.cwd() / 'dist' / 'dmg'}"
            )

        if len(dmg_files) > 1:
            raise RuntimeError(
                "Multiple DMG files found; specify one with --path:\n"
                + "\n".join(str(p) for p in dmg_files)
            )

        path = str(dmg_files[0].resolve())

    sign_dmg(dmg_path=path, p12_base64=p12_file, p12_password=p12_password)
'''
if __name__ == "__main__":
    app()
