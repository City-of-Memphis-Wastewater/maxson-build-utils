# src/maxson_build_utils/logging_setup.py
from __future__ import annotations
import logging
import sys
import traceback
from pathlib import Path

from .context import APP_DIR, APP_NAME, IMPORT_NAME, LOG_FILE_PATH

def get_logger():
    logger = logging.getLogger(IMPORT_NAME)
    return logger

def get_log_file_path() -> Path | None:
    # Resolve your log path dynamically based on context or pyproject locations.
    # Return None safely if no valid log path exists.
    pass 

def configure_logging_for_application(debug: bool = False, verbose: bool = False) -> None:
    """Configures the application-level logger using standard built-in formats."""
    INTENT="app"
    logger = get_logger()
    # Priority: debug > verbose (info) > default (WARNING)
    if debug:
        level = logging.DEBUG
        fmt = "%(levelname)-7s %(message)s"  # Left-aligned level name for neatness
    elif verbose:
        level = logging.INFO
        fmt = "%(message)s"
    else:
        level = logging.WARNING
        fmt = "%(levelname)s: %(message)s"

    logger.setLevel(level)

    # Prevent leakage to root logger
    logger.propagate = False

    # Safely clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Route strictly to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)

    logger.debug("Debug logging enabled for app.")
    logger.info("Verbose logging enabled for app.")


def configure_logging_for_library(debug: bool = False, verbose: bool = False) -> None:
    """Configures namespace logging for a library.
    
    Sets a library's log level and ensures messages propagate to the host
    application. A StreamHandler is attached as a fallback ONLY if the host
    application has no active handlers configured.
    """
    INTENT="library"
    logger = get_logger()
    # Priority: debug > verbose (info) > default (WARNING)
    if debug:
        level = logging.DEBUG
        fmt = "%(levelname)-7s %(message)s"  # Left-aligned level name for neatness
    elif verbose:
        level = logging.INFO
        fmt = "%(message)s"
    else:
        level = logging.WARNING
        fmt = "%(levelname)s: %(message)s"

    logger.setLevel(level)

    # propogate up to host applications root logger
    logger.propagate = True

    # 3. Fallback: Only add a handler if no root or parent loggers have handlers set
    root_has_handlers = bool(logging.getLogger().handlers)
    parent_has_handlers = any(h for p in logger.parent.handlers) if logger.parent else False

    if not (root_has_handlers or parent_has_handlers or logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    logger.debug(f"Library logger '{IMPORT_NAME}' level set to {logging.getLevelName(level)}.")


def log_traceback(logger_instance):
    if logger_instance.level <= logging.DEBUG:
        traceback.print_exc(file=sys.stderr)


# --- Error Logging (File Bound) ---

def setup_error_logger():
    """Configures a basic file logger that records warnings and errors."""
    error_log = logging.getLogger('')
    error_log.setLevel(logging.WARNING)
    error_log.propagate = False

    # Check if file handler already exists to prevent duplicates
    if (LOG_FILE_PATH is not None) and (not any(isinstance(h, logging.FileHandler) for h in error_log.handlers)):
        file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        error_log.addHandler(file_handler)

    return error_log

# error_logger = setup_error_logger()
