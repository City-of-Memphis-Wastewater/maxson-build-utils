#!/usr/bin/env python3
# src/maxson_build_utils/builders/pyinstaller.py

"""
Modular build execution orchestrator for PyInstaller, AppImage, and DMG workflows.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pyhabitat

from ..helpers import form_dynamic_name, PyinsMode
from ..state import export_build_env_vars

logger = logging.getLogger(__name__)


DIST_DIR = Path("dist")
DIST_DIR_ONEFILE = DIST_DIR / PyinsMode.ONEFILE.value
DIST_DIR_ONEDIR = DIST_DIR / PyinsMode.ONEDIR.value
STANDARD_MACOS_APP_DIST_DIR = DIST_DIR
BUILD_DIR = Path("build/pyinstaller_work")
RC_TEMPLATE = Path("build_assets") / "version.rc.template"
RC_FILE = Path("build_assets") / "version.rc"
PROJECT_ROOT = Path.cwd()
HOOKS_DIR_ABS = PROJECT_ROOT / "pyinstaller_hooks"


def generate_rc_file(package_version: str) -> None:
    """Generates the .rc file using the provided version string on Windows."""
    if not pyhabitat.on_windows():
        return

    if not RC_TEMPLATE.exists():
        logger.warning("RC template not found at %s. Skipping version info.", RC_TEMPLATE)
        return

    logger.info("Generated resource file %s for version %s", RC_FILE, package_version)
    RC_FILE.write_text("// Placeholder content for versioning", encoding="utf-8")


def setup_dirs() -> None:
    """Ensures intermediate and output distribution directories exist."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR_ONEFILE.mkdir(parents=True, exist_ok=True)
    DIST_DIR_ONEDIR.mkdir(parents=True, exist_ok=True)


def determine_file_extension(is_windowed_build: bool) -> str:
    """Determines binary output extension based on target system and window flag."""
    if pyhabitat.on_windows():
        return ".exe"
    elif pyhabitat.on_macos() and is_windowed_build:
        return ".app"
    return ""


def clean_artifacts(exe_name: str, mode: PyinsMode, file_extension: str) -> None:
    """Cleans previous build outputs and temporary work directories."""
    target = (
        DIST_DIR_ONEDIR / exe_name
        if mode == PyinsMode.ONEDIR
        else DIST_DIR_ONEFILE / f"{exe_name}{file_extension}"
    )

    if target.exists():
        logger.info("Removing old build artifact: %s", target.resolve())
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    if BUILD_DIR.exists():
        logger.info("Removing build work folder: %s", BUILD_DIR.resolve())
        shutil.rmtree(BUILD_DIR)

    if pyhabitat.on_windows() and RC_FILE.exists():
        RC_FILE.unlink()

def determine_app_filepath_and_dist_path(
    executable_descriptor: str, mode: PyinsMode, is_windowed_build: bool
) -> tuple[str, Path, Path, str]:
    """Calculates distribution targets and final artifact file paths."""
    ext = determine_file_extension(is_windowed_build)
    app_filename = f"{executable_descriptor}{ext}"

    if mode == PyinsMode.ONEFILE:
        dist_path = DIST_DIR_ONEFILE
        app_filepath = DIST_DIR_ONEFILE / app_filename
    else:
        if pyhabitat.on_macos():
            dist_path = STANDARD_MACOS_APP_DIST_DIR
            app_filepath = STANDARD_MACOS_APP_DIST_DIR / app_filename
        else:
            dist_path = DIST_DIR_ONEDIR
            app_filepath = DIST_DIR_ONEDIR / executable_descriptor / app_filename

    dist_path.mkdir(parents=True, exist_ok=True)
    logger.info("Executable target path: %s", app_filepath.resolve())
    return app_filename, dist_path, app_filepath, ext


def construct_pyinstaller_command(
    executable_descriptor: str,
    dist_path: Path,
    mode: PyinsMode,
    main_script_path: Path,
    is_windowed_build: bool,
    src_folder_name: str,
    icon_ico_path: Path | None = None,
    icon_icns_path: Path | None = None,
    collect_data_pkgs: list[str] | set[str] | None = None,
    collect_binary_pkgs: list[str] | set[str] | None = None,
) -> list[str]:
    """Constructs the PyInstaller CLI argument array."""
    base_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        f"--name={executable_descriptor}",
        f'--paths={PROJECT_ROOT / "src"}',
        f"--distpath={dist_path}",
        f'--workpath={BUILD_DIR / "work"}',
        f"--specpath={BUILD_DIR}",
    ]

    # Explicit data directory check
    data_dir = PROJECT_ROOT / "src" / src_folder_name / "data"
    if data_dir.exists():
        base_command.append(f"--add-data={data_dir}{os.path.pathsep}{src_folder_name}/data")

    # Safely attach hooks directory only if present in target project
    if HOOKS_DIR_ABS.exists() and HOOKS_DIR_ABS.is_dir():
        base_command.append(f"--additional-hooks-dir={HOOKS_DIR_ABS}")

    # Process dynamic package collection flags
    for pkg in collect_data_pkgs or []:
        base_command.append(f"--collect-data={pkg}")

    for pkg in collect_binary_pkgs or []:
        base_command.append(f"--collect-binaries={pkg}")

    base_command.append(f"--{mode.value}")

    if is_windowed_build:
        base_command.append("--windowed")
    else:
        logger.info("Building without --windowed flag (favoring CLI usage).")

    if pyhabitat.on_windows():
        if RC_FILE.exists():
            base_command.append(f"--version-file={RC_FILE.resolve()}")
        if icon_ico_path and icon_ico_path.exists():
            base_command.append(f"--icon={icon_ico_path.resolve()}")

    if pyhabitat.on_macos() and icon_icns_path and icon_icns_path.exists():
        base_command.append(f"--icon={icon_icns_path.resolve()}")

    base_command.append(str(main_script_path.resolve()))
    return base_command


def run_pyinstaller(
    executable_descriptor: str,
    main_script_path: Path,
    src_folder_name: str,
    mode: PyinsMode = PyinsMode.ONEDIR, # it very important that ONEDIR is the default
    is_windowed_build: bool = True,
    icon_ico_path: Path | None = None,
    icon_icns_path: Path | None = None,
    collect_data_pkgs: list[str] | set[str] | None = None,
    collect_binary_pkgs: list[str] | set[str] | None = None,
) -> tuple[Path, str]:
    """Executes the PyInstaller command within a subshell."""
    logger.info("--- %s Executable Builder ---", src_folder_name)
    app_filename, dist_path, app_filepath, ext = determine_app_filepath_and_dist_path(
        executable_descriptor, mode, is_windowed_build
    )

    clean_artifacts(exe_name=executable_descriptor, mode=mode, file_extension=ext)
    setup_dirs()

    full_command = construct_pyinstaller_command(
        executable_descriptor=executable_descriptor,
        dist_path=dist_path,
        mode=mode,
        main_script_path=main_script_path,
        is_windowed_build=is_windowed_build,
        src_folder_name=src_folder_name,
        icon_ico_path=icon_ico_path,
        icon_icns_path=icon_icns_path,
        collect_data_pkgs=collect_data_pkgs,
        collect_binary_pkgs=collect_binary_pkgs,
    )

    logger.info("Executing command: %s", " ".join(full_command))
    try:
        subprocess.run(full_command, check=True, env=os.environ.copy())
    except subprocess.CalledProcessError as e:
        logger.error("PyInstaller failed with exit code %d", e.returncode)
        raise SystemExit(e.returncode) from e

    if pyhabitat.on_macos() and mode == PyinsMode.ONEDIR:
        duplicate_cli_dir = DIST_DIR / executable_descriptor
        if duplicate_cli_dir.exists() and duplicate_cli_dir.is_dir():
            shutil.rmtree(duplicate_cli_dir)

    return app_filepath.resolve(), app_filename


def run_build_executable(
    src_folder_name: str,
    version: str,
    mode: PyinsMode = PyinsMode.ONEDIR,
    is_windowed_build: bool | None = None,
    icon_ico_path: Path | None = None,
    icon_icns_path: Path | None = None,
    collect_data_pkgs: list[str] | set[str] | None = None,
    collect_binary_pkgs: list[str] | set[str] | None = None,
) -> tuple[Path, str]:
    """Primary entry point for downstream project packaging scripts."""

    if not version or version == "0.0.0":
        logger.error("FATAL: Invalid package version provided.")
        sys.exit(1)

    if not is_windowed_build:
        is_windowed_build = (
            (pyhabitat.on_windows() or pyhabitat.on_macos())
            and (mode == PyinsMode.ONEDIR)
            and pyhabitat.tkinter_is_available()
        )

    try:
        if version == "0.0.0" or not version:
            logger.error("FATAL: Invalid package version provided.")
            sys.exit(1)

        from maxson_build_utils import MaxsonPyProject
        _pyproject = MaxsonPyProject()

        generate_rc_file(version)
        executable_descriptor = form_dynamic_name(pkg_name=src_folder_name, version=version, mode=mode)
        #cli_main_file = get_cli_main_file(project_root=PROJECT_ROOT, src_folder_name=src_folder_name)
        cli_main_file =_pyproject.src_dir / "__main__.py"

        app_filepath, app_filename = run_pyinstaller(
            executable_descriptor=executable_descriptor,
            main_script_path=cli_main_file,
            src_folder_name=src_folder_name,
            mode=mode,
            is_windowed_build=is_windowed_build,
            icon_ico_path=icon_ico_path,
            icon_icns_path=icon_icns_path,
            collect_data_pkgs=collect_data_pkgs,
            collect_binary_pkgs=collect_binary_pkgs,
        )

        # Export dynamic ONEDIR directory and binary name
        #if mode == PyinsMode.ONEDIR:
        export_build_env_vars(app_filepath=app_filepath, executable_descriptor=executable_descriptor)
        
        return app_filepath, app_filename
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        logger.error("An unhandled error occurred during build: %s", e, exc_info=True)
        sys.exit(1)
