# src/maxson_build_utils/builders/shiv.py
from __future__ import annotations

import os
import shutil
import site
import subprocess
import sys
import tempfile
from pathlib import Path
import pyhabitat

from ..helpers import form_dynamic_name
from ..cli_utils import get_cli_commands
from ..pyproject import MaxsonPyProject
from ..context import get_pyproject

def run_command(cmd: list[str], check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run command with logging and error reporting."""
    print(f"\n$ {' '.join(cmd)}")
    final_env = env if env is not None else os.environ.copy()

    result = subprocess.run(cmd, text=True, check=False, capture_output=True, env=final_env)

    if result.stdout:
        print(result.stdout.strip())

    if result.returncode != 0:
        if result.stderr:
            print(f"--- COMMAND FAILED (Exit {result.returncode}) ---", file=sys.stderr)
            print(result.stderr.strip(), file=sys.stderr)

        if check:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
    return result


def find_latest_wheel(dist_dir: Path, src_folder_name: str, version: str) -> Path:
    """Finds the most recently built wheel file for the given package and version."""
    wheels = sorted(
        dist_dir.glob(f"{src_folder_name}-{version}*.whl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not wheels:
        raise FileNotFoundError(f"No wheel found for {src_folder_name} version {version} in {dist_dir}.")
    return wheels[0]


def ensure_dependencies_and_shiv() -> None:
    """Ensures environment dependencies and 'shiv' are installed and accessible."""
    if os.environ.get("CI") == "true":
        print("\nSkipping dependency check/install inside CI environment.")
        return

    print("Syncing dev group dependencies via uv...")
    run_command(["uv", "sync", "--group", "dev"])

    try:
        run_command(["uv", "run", "shiv", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("Installing 'shiv'...")
        run_command(["uv", "add", "shiv"])


def create_windows_bat_launcher(
    pyz_filename: str, output_dir: Path, has_gui: bool
) -> None:
  """Creates a Windows BAT file launcher for GUI execution when running on Windows."""
  if os.name != "nt" or not has_gui:
    return

  bat_filename = pyz_filename.replace(".pyz", "-gui.bat")
  bat_path = output_dir / bat_filename

  bat_content = f"""@echo off
rem Launch {pyz_filename} with the 'gui' command using system Python.
python "%~dp0{pyz_filename}" gui
"""
  try:
    bat_path.write_text(bat_content, encoding="utf-8")
    print(f"Created Windows BAT launcher: {bat_path.name}")
  except Exception as e:
    print(f"WARNING: Failed to create BAT launcher: {e}", file=sys.stderr)

def test_pyz_gui(output_path: Path):
    print(f"Testing GUI mode for {output_path.name}...")
    run_command([sys.executable, str(output_path), "gui", "--auto-close", "1000"], check=True)


def run_build_pyz(
    root_dir: Path = Path.cwd(),
    src_folder_name: str | None = None,
    version: str | None = None,
    entry_point: str | None = None,
    dist_dir: Path = Path("dist") / "zipapp",
    test_gui: bool = True,
) -> Path:
    """Builds a portable Python ZipApp (PYZ) using shiv and verifies the output artifact."""
    if version == "0.0.0":
        raise ValueError("Cannot proceed without a valid version string.")

    dist_dir.mkdir(parents=True, exist_ok=True)

    pyproject = MaxsonPyProject(path=root_dir)
    if src_folder_name is None:
        src_folder_name = pyproject.import_name
    if version is None:
        version = pyproject.version

    #scripts = pyproject.get("project", "scripts")
    #f"{pyproject.import_name}.__main__:app"
    if entry_point is None:
        entry_point = pyproject.get("project", "scripts",f"{pyproject.import_name}")

    # Configure isolated temporary root for Shiv internal caching
    build_temp = Path(tempfile.gettempdir()) / "shiv_build"
    if build_temp.exists():
        shutil.rmtree(build_temp, ignore_errors=True)
    build_temp.mkdir(parents=True, exist_ok=True)
    os.environ["SHIV_ROOT"] = str(build_temp)

    # 1. Sync dependencies
    ensure_dependencies_and_shiv()

    # 2. Build Wheel into target zipapp directory
    print("\nBuilding project wheel via uv build...")
    custom_env = os.environ.copy()
    if pyhabitat.on_termux():
        termux_tmp = Path.home() / ".tmp"
        termux_tmp.mkdir(exist_ok=True)
        custom_env["TMPDIR"] = str(termux_tmp)

    run_command(["uv", "build", "--wheel", "--out-dir", str(dist_dir)], env=custom_env)

    # 3. Locate wheel and construct Shiv command
    wheel_path = find_latest_wheel(dist_dir, src_folder_name, version)
    dynamic_name = form_dynamic_name(pkg_name=src_folder_name, version=version, mode=None)
    pyz_filename = f"{dynamic_name}-shiv.pyz"
    interpreter = "python" if os.name == "nt" else "/usr/bin/env python3"
    output_path = dist_dir / pyz_filename

    if output_path.exists():
        output_path.unlink()

    cmd = [
        "uv", "run", "shiv",
        "-o", str(output_path),
        "-p", interpreter,
        "-e", entry_point,
        "--compressed",
        "--no-cache",
        str(wheel_path),
    ]

    print(f"\nBuilding PYZ using shiv from Wheel: {pyz_filename}")
    run_command(cmd, env=custom_env)
    output_path.chmod(0o755)

    # Cleanup staging wheel
    try:
        wheel_path.unlink()
        print(f"Removed staging wheel: {wheel_path.name}")
    except Exception as e:
        print(f"Note: Could not delete temporary wheel: {e}")


    # ---
    # Inspect commands to conditionally handle GUI launch and testing
    available_commands = get_cli_commands(entry_point)
    has_gui_command = "gui" in available_commands

    create_windows_bat_launcher(pyz_filename, dist_dir, has_gui=has_gui_command)

    # 4. Post-build verification
    print("\nTesting generated Shiv artifact...")
    run_command([sys.executable, str(output_path), "--help"], check=True)

    if (
        test_gui
        and has_gui_command
        and pyhabitat.tkinter_is_available()
    ):
        test_pyz_gui(output_path)
    elif test_gui and not has_gui_command:
        print("Skipping GUI test: 'gui' subcommand is not registered on this CLI.")
    # ---
    """
    create_windows_bat_launcher(pyz_filename, dist_dir)

    # 4. Post-build verification
    print("\nTesting generated Shiv artifact...")
    run_command([sys.executable, str(output_path), "--help"], check=True)

    if test_gui and pyhabitat.tkinter_is_available():
        test_pyz_gui(output_path)
    """
    print(f"\nBuild complete! Portable PYZ: {output_path.resolve()}")
    return output_path
