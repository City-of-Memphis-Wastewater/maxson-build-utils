# src/dworshak_secret/logging_setup.py
from __future__ import annotations
import logging
import sys
import traceback
from rich.logging import RichHandler
from rich.console import Console
console = Console(stderr=True)

logger = logging.getLogger("dworshak_secret")

def configure_logging_for_application(debug: bool=False,verbose: bool=False):
    INTENT="subapp"

    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = RichHandler(console=console, show_time=False, show_path=debug,log_time_format="[%H:%M:%S]")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.debug(f"Debug logging enabled for {INTENT}.")
    logger.info(f"Verbose logging enabled for {INTENT}.")

def setup_logging(verbose: bool = False, debug: bool = False, initial: bool=False):
    """
    Defunct.

    Configure the root 'dworshak_prompt' logger.
    Priority: debug > verbose > default (WARNING)

    Defunct.

    """
    logger = logging.getLogger()

    # Clear any existing handlers to prevent duplicates
    logger.handlers.clear()

    # Choose level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Simple, clean format (no timestamps unless debug)
    if debug:
        formatter = logging.Formatter('%(levelname)s [%(name)s] %(message)s  (%(filename)s:%(lineno)d)')
    else:
        formatter = logging.Formatter('%(message)s')

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional: file logging (uncomment if you want persistent logs)
    # file_handler = logging.FileHandler("dworshak.log")
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s'))
    # logger.addHandler(file_handler)
    if initial:
        logger.debug("Logging initialized at level %s", logging.getLevelName(level))
    return logger


def log_traceback(logger):
    if logger.level <= logging.DEBUG:
        traceback.print_exc(file=sys.stderr)
