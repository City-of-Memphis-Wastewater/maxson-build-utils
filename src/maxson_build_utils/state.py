# src/maxson_build_utils/state.py
import os
from pathlib import Path

def export_build_env_vars(app_path: Path, executable_descriptor: str) -> None:
    """Exports dynamic PyInstaller paths to os.environ and GitHub Actions runner state."""
    env_vars = {
        "PYINSTALLER_ONEDIR_BUILD_DIR": str(app_path),
        "EXECUTABLE_DESCRIPTOR": executable_descriptor,
        "PYINSTALLER_ONEDIR_EXE_NAME": executable_descriptor,
    }

    for key, value in env_vars.items():
        # Local process environment
        os.environ[key] = value

        # GitHub Actions step environment ($GITHUB_ENV)
        if gha_env := os.environ.get("GITHUB_ENV"):
            with open(gha_env, "a", encoding="utf-8") as f:
                f.write(f"{key}={value}\n")

        # GitHub Actions step outputs ($GITHUB_OUTPUT)
        if gha_output := os.environ.get("GITHUB_OUTPUT"):
            with open(gha_output, "a", encoding="utf-8") as f:
                f.write(f"{key.lower()}={value}\n")

def get_pyinstaller_onedir_exe_filename():
    return os.environ.get("EXE_NAME")

def get_pyinstaller_onedir_build_dir():
    return os.environ.get("PYINSTALLER_ONEDIR_BUILD_DIR")