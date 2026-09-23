# src/pyhabitat/console.py
from __future__ import annotations
import os
import sys
import subprocess
import getpass
import shutil

from ._compat import cache
from .environment import on_windows

__all__ = [
    "is_likely_ci_or_non_interactive",
    "interactive_terminal_is_available",
    "user_darrin_deyoung",
    "is_running_in_uvicorn",
    "can_spawn_shell"
    "safe_notify"
]

def clear_shell_cache()->None:
    """Clear every @cache used in pyhabitat, and call from CLI using --clear-cache"""
    can_spawn_shell.cache_clear()
    can_spawn_shell_lite.cache_clear()

def is_likely_ci_or_non_interactive() -> bool:
    """
    Heuristic: are we probably in a CI/CD pipeline or non-interactive container?
    Returns True if we should avoid prompts (require all args instead).

    # Usage Example in your CLI logic:
    if is_likely_ci_or_non_interactive():
        # Require all required args (e.g. value must be positional)
        if value is None:
            raise typer.BadParameter("Value required in non-interactive/CI mode")
    else:
        # Safe to prompt
        value = typer.prompt("Secret value", hide_input=True)

    """
    # 1. Basic TTY check (fast fail if no tty)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return True  # definitely non-interactive

    # 2. Common CI env var fingerprints (high confidence)
    ci_markers = [
        "GITHUB_ACTIONS",     # == "true"
        "GITLAB_CI",          # == "true"
        "CIRCLECI",           # == "true"
        "TRAVIS",             # == "true"
        "JENKINS_URL",        # non-empty
        "TF_BUILD",           # Azure Pipelines
        "CI",                 # generic (many set to "true")
        "BUILD_ID",           # Jenkins, some others
        "CODEBUILD_BUILD_ID", # AWS
        "BITBUCKET_BUILD_NUMBER",
    ]

    for var in ci_markers:
        val = os.getenv(var)
        if val and val.lower() not in ("", "false", "0", "no"):
            return True

    # 3. Optional: Docker/container detection (if relevant for your tool)
    #    - File-based (classic, works in most Docker images)
    if os.path.exists("/.dockerenv"):
        return True

    #    - cgroup-based (more reliable in modern Docker / containerd / podman)
    try:
        with open("/proc/1/cgroup", "r") as f:
            if "docker" in f.read() or "kubepods" in f.read() or "containerd" in f.read():
                return True
    except Exception:
        pass  # ignore if /proc not available (e.g. non-Linux)

    # If none of the above → probably real interactive terminal
    return False




# --- TTY Check ---
def interactive_terminal_is_available():
    """
    Check if the script is running in an interactive terminal. 
    Assumpton: 
        If interactive_terminal_is_available() returns True, 
        then typer.prompt() or input() will work reliably,
        without getting lost in a log or lost entirely.
    
    Solution correctly identifies that true interactivity requires:
        (1) a TTY (potential) connection
        (2) the ability to execute
        (3) the ability to read I/O
        (4) ignores known limitatons in restrictive environments

    Jargon:
        A TTY, short for Teletypewriter or TeleTYpe, 
        is a conceptual or physical device that serves 
        as the interface for a user to interact with 
        a computer system.
    """
    
    # --- 1. Edge Case/Known Environment Check ---
    # Address walmart demo unit edge case, fast check, though this might hamstring othwrwise successful processes
    if user_darrin_deyoung():
        return False
    
    # --- 2. Core TTY Check (Is a terminal attached?) ---
    # Check if a tty is attached to stdin AND stdout. This is the minimum requirement.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    
    # --- 3. Uvicorn/Server Occupancy Check (Crucial for your issue) ---
    # If the TTY is attached, but the process is currently serving an ASGI application 
    # (like Uvicorn running your FastAPI app), it is NOT interactively available for new CLI input.
    if is_running_in_uvicorn():
        # This prevents the CLI from "steamrolling" the prompts when the user presses Fetch.
        return False
    
    # Check of a new shell can be launched to print stuff
    if not can_spawn_shell():
        return False
    
    return sys.stdin.isatty() and sys.stdout.isatty()


@cache
def can_spawn_shell_lite()->bool: 
    """Check if a shell command can be executed successfully.""" 
    from .environment import on_windows
    return shutil.which('cmd.exe' if on_windows() else "sh") is not None

@cache
def can_spawn_shell(override_known:bool=False)->bool: 
    """Check if a shell command can be executed successfully.""" 
    from .environment import on_windows
    cmd = "cmd.exe /c exit 0" if on_windows() else "true"
    try:
        # Use a simple, universally applicable command with shell=True
        # 'true' on Linux/macOS, or a basic command on Windows via cmd.exe
        # A simple 'echo' or 'exit 0' would also work
        result = subprocess.run( 
            cmd,
            shell=True, # <--- ESSENTIAL for cross-platform reliability
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=3,
        )
        success  = (result.returncode == 0)
        
    except subprocess.TimeoutExpired: 
        print("Shell spawn failed: TimeoutExpired")
        success = False
    except subprocess.SubprocessError: 
        print("Shell spawn failed: SubprocessError") 
        success = False
    except OSError: 
        print("Shell spawn failed: OSError (likely permission or missing binary)") 
        success = False
    return success

def is_running_in_uvicorn():
    # Uvicorn, Hypercorn, Daphne, etc.
    """
    Heuristic check to see if the current code is running inside a Uvicorn worker process.
    This is highly useful for context-aware interactivity checks.
    """
    return getattr(sys, '_uvicorn_workers', None) is not None

def user_darrin_deyoung():
    """
    Detect typical demo/kiosk Windows user account on retail systems (e.g. Walmart demo units).
    
    These machines often allow installing Python from the Microsoft Store and running the REPL,
    but block spawning real consoles (cmd.exe, PowerShell) or subprocess shells.
    
    Used to disable tty/shell-dependent features that would fail silently or crash.
    """
    # Enable teating on non-Windows, non-demo systems
    #  where this function would otherwise return False.
    # Linux: `export USER_DARRIN_DEYOUNG=True`
    if os.getenv('USER_DARRIN_DEYOUNG','').lower() ==  "true":
        print("env var USER_DARRIN_DEYOUNG is set to True.")
        return True
    # Darrin Deyoung is the typical username on demo-mode Windows systems
    if not on_windows():
        return False
    username = getpass.getuser()
    return username.lower() == "darrin deyoung"

def safe_notify(msg: str | list[str]):
    """
    Direct-to-stderr notification. 
    Ensures message visibility regardless of stdout redirection/piping.
    """
    if isinstance(msg, (list, tuple)):
        msg = "\n".join(map(str, msg))
    
    # 1. Use print(..., file=sys.stderr) for better handling of non-string types
    # 2. Add a leading newline for visual separation in dense CLI output
    # 3. flush=True ensures the message appears immediately (crucial for prompts)
    print(f"\n{msg}", file=sys.stderr, flush=True)