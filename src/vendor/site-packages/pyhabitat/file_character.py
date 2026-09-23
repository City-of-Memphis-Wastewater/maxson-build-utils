# src/pyhabitat/environment.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import platform
import sys
import os
import webbrowser
import shutil
from pathlib import Path
import subprocess
import io
import zipfile
import logging
from typing import Optional


# On Windows, we need the msvcrt module for non-blocking I/O
try:
    import msvcrt
except ImportError:
    msvcrt = None

__all__ = [
    'is_elf',
    'is_pyz',
    'is_windows_portable_executable',
    'is_macos_executable',
    'is_pipx',
    'is_python_script',
    'is_in_git_repo',
    'read_magic_bytes',
    'check_executable_path',
]


# --- Binary Characteristic Checks ---
def is_elf(exec_path: Path | str | None = None, debug: bool = False, suppress_debug: bool =False) -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a standalone PyInstaller-built ELF binary."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    exec_path, is_valid = check_executable_path(exec_path, debug and not suppress_debug)
    if not is_valid:
        return False
    
    try:
        # Check the magic number: The first four bytes of an ELF file are 0x7f, 'E', 'L', 'F' (b'\x7fELF').
        # This is the most reliable way to determine if the executable is a native binary wrapper (like PyInstaller's).
        magic_bytes = read_magic_bytes(exec_path, 4, debug and not suppress_debug)
        if magic_bytes is None:
            return False
        return magic_bytes == b'\x7fELF'
    except (OSError, IOError) as e:
        if debug:
            logging.debug("False (Exception during file check)")
        return False
    
def is_pyz(exec_path: Path | str | None = None, debug: bool = False, suppress_debug: bool =False) -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a PYZ zipapp ."""

    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    exec_path, is_valid = check_executable_path(exec_path, debug and not suppress_debug)
    if not is_valid:
        return False
    
    # Check if the extension is PYZ
    if not str(exec_path).endswith(".pyz"):
        if debug:
            logging.debug("is_pyz()=False (Not a .pyz file)")
        return False

    if not _check_if_zip(exec_path):
        if debug:
            logging.debug("False (Not a valid ZIP file)")
        return False

    return True

def is_windows_portable_executable(exec_path: Path | str | None = None, debug: bool = False, suppress_debug: bool =False) -> bool:
    """
    Checks if the specified path or sys.argv[0] is a Windows Portable Executable (PE) binary.
    Windows Portable Executables include .exe, .dll, and other binaries.
    The standard way to check for a PE is to look for the MZ magic number at the very beginning of the file.
    """
    exec_path, is_valid = check_executable_path(exec_path, debug and not suppress_debug)
    if not is_valid:
        return False
    try:
        magic_bytes = read_magic_bytes(exec_path, 2, debug and not suppress_debug)
        if magic_bytes is  None:
            return False
        result = magic_bytes.startswith(b"MZ")
        return result
    except (OSError, IOError) as e:
        if debug:
            logging.debug(f"is_windows_portable_executable() = False (Exception: {e})")
        return False


def is_macos_executable(exec_path: Path | str | None = None, debug: bool = False, suppress_debug: bool =False) -> bool:
    """
    Checks if the currently running executable is a macOS/Darwin Mach-O binary, 
    and explicitly excludes pipx-managed environments.
    """
    exec_path, is_valid = check_executable_path(exec_path, debug and not suppress_debug)
    if not is_valid:
        return False
        
    try:
        # Check the magic number: Mach-O binaries start with specific 4-byte headers.
        # Common ones are: b'\xfe\xed\xfa\xce' (32-bit) or b'\xfe\xed\xfa\xcf' (64-bit)
        
        magic_bytes = read_magic_bytes(exec_path, 4, debug and not suppress_debug)
        if magic_bytes is None:
            return False
        # Common Mach-O magic numbers (including their reversed-byte counterparts)
        MACHO_MAGIC = {
            b'\xfe\xed\xfa\xce',  # MH_MAGIC
            b'\xce\xfa\xed\xfe',  # MH_CIGAM (byte-swapped)
            b'\xfe\xed\xfa\xcf',  # MH_MAGIC_64
            b'\xcf\xfa\xed\xfe',  # MH_CIGAM_64 (byte-swapped)
        }
        
        is_macho = magic_bytes in MACHO_MAGIC
        
            
        return is_macho
        
    except (OSError, IOError) as e:
        if debug:
            logging.debug("is_macos_executable() = False (Exception during file check)")
        return False


def is_pipx(exec_path: Path | str | None = None, debug: bool = False, suppress_debug: bool = True) -> bool:
    """Checks if the executable is running from a pipx managed environment."""
    exec_path, is_valid = check_executable_path(exec_path, debug and not suppress_debug, check_pipx=False)
    # check_pipx arg should be false when calling from inside of is_pipx() to avoid recursion error
    # For safety, check_executable_path() guards against this.
    if not is_valid:
        return False
        
    try:
        interpreter_path = Path(sys.executable).resolve()
        pipx_bin_path, pipx_venv_base_path = _get_pipx_paths()

        # Normalize paths for comparison
        norm_exec_path = str(exec_path).lower()
        norm_interp_path = str(interpreter_path).lower()
        pipx_venv_base_str = str(pipx_venv_base_path).lower()

        if debug:
            logging.debug(f"EXEC_PATH: {exec_path}")
            logging.debug(f"INTERP_PATH: {interpreter_path}")
            logging.debug(f"PIPX_BIN_PATH: {pipx_bin_path}")
            logging.debug(f"PIPX_VENV_BASE: {pipx_venv_base_path}")
            is_in_pipx_venv_base = norm_interp_path.startswith(pipx_venv_base_str)
            logging.debug(f"Interpreter path resides somewhere within the pipx venv base hierarchy: {is_in_pipx_venv_base}")
            logging.debug(
                f"This determines whether the current interpreter is managed by pipx: {is_in_pipx_venv_base}"
            )
        if "pipx/venvs" in norm_exec_path or "pipx/venvs" in norm_interp_path:
            if debug:
                logging.debug("is_pipx() is True // Signature Check")
            return True

        if norm_interp_path.startswith(pipx_venv_base_str):
            if debug:
                logging.debug("is_pipx() is True // Interpreter Base Check")
            return True

        if norm_exec_path.startswith(pipx_venv_base_str):
            if debug:
                logging.debug("is_pipx() is True // Executable Base Check")
            return True

        if debug:
            logging.debug("is_pipx() is False")
        return False

    except Exception:
        if debug:
            logging.debug("False (Exception during pipx check)")
    
def is_python_script(path: Path | str | None = None, debug: bool = False, suppress_debug: bool =False) -> bool:
    """
    Checks if the specified path or running script is a Python source file (.py).

    By default, checks the running script (`sys.argv[0]`). If a specific `path` is
    provided, checks that path instead. Uses `Path.resolve()` for stable path handling.

    Args:
        path: Optional; path to the file to check (str or Path). If None, defaults to `sys.argv[0]`.
        debug: If True, prints the path being checked.

    Returns:
        bool: True if the specified or default path is a Python source file (.py); False otherwise.
    """
    exec_path, is_valid = check_executable_path(path, debug and not suppress_debug, check_pipx=False)
    if not is_valid:
        return False
    return exec_path.suffix.lower() == '.py'    

# --- File encoding check ---
def is_binary(path:str|Path|None=None)->bool:
    """
    Target file is encoded as binary.
    """
    pass

def is_ascii(path:str|Path|None=None)->bool:
    """
    Target file is encoded as ascii, plaintext.
    """
    pass

def read_magic_bytes(path: str, length: int = 4, debug: bool = False) -> bytes | None:
    """Return the first few bytes of a file for type detection.
    Returns None if the file cannot be read or does not exist.
    """
    try:
        with open(path, "rb") as f:
            magic = f.read(length)
        if debug:
            logging.debug(f"Magic bytes: {magic!r}")
        return magic
    except Exception as e:
        if debug:
            logging.debug(f"False (Error during file check: {e})")
        #return False # not typesafe
        #return b'' # could be misunderstood as what was found
        return None # no way to conflate that this was a legitimate error
    
def _get_pipx_paths():
    """
    Returns the configured/default pipx binary and home directories.
    Assumes you indeed have a pipx dir.
    """
    # 1. PIPX_BIN_DIR (where the symlinks live, e.g., ~/.local/bin)
    pipx_bin_dir_str = os.environ.get('PIPX_BIN_DIR')
    if pipx_bin_dir_str:
        pipx_bin_path = Path(pipx_bin_dir_str).resolve()
    else:
        # Default binary path (common across platforms for user installs)
        pipx_bin_path = Path.home() / '.local' / 'bin'

    # 2. PIPX_HOME (where the isolated venvs live, e.g., ~/.local/pipx/venvs)
    pipx_home_str = os.environ.get('PIPX_HOME')
    if pipx_home_str:
        # PIPX_HOME is the base, venvs are in PIPX_HOME/venvs
        pipx_venv_base = Path(pipx_home_str).resolve() / 'venvs'
    else:
        # Fallback to the modern default for PIPX_HOME (XDG standard)
        # Note: pipx is smart and may check the older ~/.local/pipx too
        # but the XDG one is the current standard.
        pipx_venv_base = Path.home() / '.local' / 'share' / 'pipx' / 'venvs'

    return pipx_bin_path, pipx_venv_base.resolve()


def _check_if_zip(path: Path | str | None) -> bool:
    """Checks if the file at the given path is a valid ZIP archive."""
    if path is None:
        return False
    path = Path(path).resolve()

    try:
        return zipfile.is_zipfile(path)
    except Exception:
        # Handle cases where the path might be invalid, or other unexpected errors
        return False

def check_executable_path(exec_path: Path | str | None, 
                           debug: bool = False, 
                           check_pipx: bool = True
) -> tuple[Path | None, bool]: #compensate with __future__, may cause type checker issues
    """
    Helper function to resolve an executable path and perform common checks.

    Returns:
        tuple[Path | None, bool]: (Resolved path, is_valid)
        - Path: The resolved Path object, or None if invalid
        - bool: Whether the path should be considered valid for subsequent checks
    """
    # 1. Determine path
    if exec_path is None:
        exec_path = Path(sys.argv[0]).resolve() if sys.argv[0] and sys.argv[0] != '-c' else None
    else:
        exec_path = Path(exec_path).resolve()

    if debug:
        logging.debug(f"Checking executable path: {exec_path}")

    # 2. Handle missing path
    if exec_path is None:
        if debug:
            logging.debug("check_executable_path() returns (None, False) // exec_path is None")
        return None, False
    
    # 3. Ensure path actually exists and is a file
    if not exec_path.is_file(): 
        if debug:
            logging.debug("check_executable_path() returns (exec_path, False) // exec_path is not a file")
        return exec_path, False

    # 4. Avoid recursive pipx check loops
    # This guard ensures we don’t recursively call check_executable_path()
    # via is_pipx() -> check_executable_path() -> is_pipx() -> ...
    if check_pipx:
        caller = sys._getframe(1).f_code.co_name
        if caller != "is_pipx":
            if is_pipx(exec_path, debug):
                if debug:
                    logging.debug("check_executable_path() returns (exec_path, False) // is_pipx(exec_path) is True")
                return exec_path, False

    return exec_path, True       

def is_in_git_repo(path: str = '.') -> Optional[bool]:
    """
    Checks if a path is in a Git repo.
    Returns:
        True: Confirmed inside a work tree.
        False: Confirmed NOT inside a work tree.
        None: Inconclusive (Git not installed, permission denied, etc.)
    The exisiting use case is to check if the source code is running from within developer environment for a typical Python project.
    
    """
    abs_path = os.path.abspath(path)
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            cwd=abs_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip() == 'true'
    
    except subprocess.CalledProcessError as e:
        # Git is installed, and it explicitly said "No" (exit code 128)
        # or we are in a subfolder that isn't a repo.
        return False
        
    except (FileNotFoundError, PermissionError):
        # The tool is missing or blocked. We don't know the answer.
        return None