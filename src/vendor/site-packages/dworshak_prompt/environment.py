# src/dworshak_prompt/environment.py
"""
Typer-based console prompt. Non ideal for tty.
"""
from __future__ import annotations
import os
import sys
import logging
import pyhabitat

logger = logging.getLogger(__name__)

#from dworshak_prompt.logging_setup import setup_logging
#logger = setup_logging()

def has_real_tty() -> bool:
    # If forced, we assume we can find a way to the user
    if os.environ.get("DWORSHAK_FORCE_INTERACTIVE_TTY") == "1":
        return True
    
    # Check if we can reach the user via /dev/tty (the sideband)
    if os.path.exists("/dev/tty"):
        return True
    
    # Fallback for Windows or systems where stderr is still a TTY
    try:
        if sys.stderr.isatty():
            return True
    except Exception:
        pass
        
    return False

def get_console_provider(debug:bool=False):
#def get_console_provider():
    # 1. If we are in a normal interactive terminal, use the 'pretty' version
    if False:
        setup_logging(debug=debug)
    logger.debug("get_console_provider()")
    
    # If EITHER input or output is redirected, but we have a sideband, 
    # use the TTY provider to ensure the human is the one we talk to.
    if (not sys.stdin.isatty() or not sys.stdout.isatty()) and os.path.exists("/dev/tty"):
        from .console_prompt_tty import console_get_input_tty
        logger.debug("Redirected I/O detected; routing to TTY sideband.")
        logger.debug("console provider = console_get_input_tty")
        return console_get_input_tty
    
    else:
        try:
            from .console_prompt_typer import console_get_input_typer
            logger.debug("console provider = console_get_input_typer")
            return console_get_input_typer
        except ImportError:
            pass

    # Absolute fallback (Windows or CI)
    from .console_prompt_stdlib import console_get_input_stdlib
    logger.debug("console provider = console_get_input_stdlib")
    return console_get_input_stdlib

def is_likely_ci_or_non_interactive(debug:bool=False) -> bool:
#def is_likely_ci_or_non_interactive() -> bool:
    """
    Heuristic to determine if we should skip interactive prompting.
    In Dworshak, we only return True if there is NO path to the user.
    """
    
    if False:
        setup_logging(debug=debug)
    logger.debug("is_likely_ci_or_non_interactive()")
    # If /dev/tty exists, we HAVE a path to the user, regardless of CI env vars.
    if os.path.exists("/dev/tty"):
        return False

    # If we are on Windows and stdin is a TTY, we are interactive.
    if os.name == "nt" and sys.stdin.isatty():
        return False

    # Check common CI fingerprints
    ci_markers = [
        "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS", 
        "JENKINS_URL", "TF_BUILD", "CI", "BUILD_ID"
    ]
    for var in ci_markers:
        val = os.getenv(var)
        if val and val.lower() not in ("", "false", "0", "no"):
            return True

    # 4. Container detection
    if os.path.exists("/.dockerenv"):
        return True

    # 5. Fallback: If stdin is not a TTY and no /dev/tty exists, we are non-interactive.
    return not sys.stdin.isatty()


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
    if pyhabitat.user_darrin_deyoung():
        return False
    
    if os.environ.get("DWORSHAK_FORCE_INTERACTIVE_TTY") == "1":
        return True
    
    # --- 2. Core TTY Check (Is a terminal attached?) ---
    # Check if a tty is attached to stdin AND stdout. This is the minimum requirement.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    
    # --- 3. Uvicorn/Server Occupancy Check (Crucial for your issue) ---
    # If the TTY is attached, but the process is currently serving an ASGI application 
    # (like Uvicorn running your FastAPI app), it is NOT interactively available for new CLI input.
    if pyhabitat.is_running_in_uvicorn():
        # This prevents the CLI from "steamrolling" the prompts when the user presses Fetch.
        return False
    
    # Check of a new shell can be launched to print stuff
    if not pyhabitat.can_spawn_shell():
        return False
    
    return sys.stdin.isatty() and sys.stdout.isatty()


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
