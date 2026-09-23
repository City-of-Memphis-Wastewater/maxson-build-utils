# src/dworshak_env/logging_setup.py
from __future__ import annotations
import logging
import sys
from rich.logging import RichHandler
from rich.console import Console
console = Console(stderr=True)

logger = logging.getLogger("dworshak_env")

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

