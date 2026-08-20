# src/maxson_build_utils/logging_setup.py
from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

from .context import IMPORT_NAME, LOG_FILE_PATH


def get_logger(name: str | None = None) -> logging.Logger:
    """Returns a logger inside the package namespace."""
    target_name = name or IMPORT_NAME
    return logging.getLogger(target_name)


def configure_logging_for_application(
    debug: bool = False,
    verbose: bool = False,
    log_to_file: bool = True,
) -> logging.Logger:
    """Configures application-level console logging and error file logging."""
    logger = get_logger()

    if debug:
        level = logging.DEBUG
        fmt = "%(levelname)-7s %(message)s"
    elif verbose:
        level = logging.INFO
        fmt = "%(message)s"
    else:
        level = logging.WARNING
        fmt = "%(levelname)s: %(message)s"

    logger.setLevel(level)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    # Terminal output (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(console_handler)

    # File output (warnings & errors)
    if log_to_file and LOG_FILE_PATH is not None:
        try:
            LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.WARNING)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as err:
            logger.warning(f"Failed to initialize file log at {LOG_FILE_PATH}: {err}")

    logger.debug("Debug logging enabled.")
    logger.info("Verbose logging enabled.")
    return logger


def configure_logging_for_library(debug: bool = False, verbose: bool = False) -> logging.Logger:
    """Configures package logging for library consumption (attaches NullHandler)."""
    logger = get_logger()

    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)
    logger.propagate = True

    # Standard Python library best practice: attach NullHandler if no handlers exist
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger

def configure_logging_all_debug() -> None:
    """Forces DEBUG logging across the current package AND all dependencies."""
    # 1. Fetch the global root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 2. Clear pre-existing handlers across third-party libraries
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 3. Create a console handler that prints logger names (%(name)s) to trace sources
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    
    # Detailed format showing timestamp, level, logger source, and message
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-7s - [%(name)s] %(message)s"
    )
    console_handler.setFormatter(formatter)

    # 4. Attach handler to root logger
    root_logger.addHandler(console_handler)


def log_traceback(logger_instance: logging.Logger) -> None:
    """Safely prints stack traces only when debug level is enabled."""
    if logger_instance.isEnabledFor(logging.DEBUG):
        traceback.print_exc(file=sys.stderr)