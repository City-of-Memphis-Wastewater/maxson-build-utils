# src/pyhabitat/logging_setup.py
from __future__ import annotations
import logging
import sys

logger = logging.getLogger("pyhabitat")

def configure_logging(debug: bool = False, info: bool = False) -> None:
    """Configures the package-level logger using standard built-in formats."""
    
    # Priority: debug > verbose > default (WARNING)
    if debug:
        level = logging.DEBUG
        fmt = "%(levelname)s (%(filename)s:%(lineno)d): %(message)s"
    elif info:
        level = logging.INFO
        fmt = "%(message)s"
    else:
        level = logging.WARNING
        fmt = "%(levelname)s: %(message)s"

    logger.setLevel(level)

    # Safely clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Route strictly to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)

    # Prevent leakage to root logger
    logger.propagate = False

    logger.debug("Debug logging initialized.")
    logger.info("Info logging initialized.")
