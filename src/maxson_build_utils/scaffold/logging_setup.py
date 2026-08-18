# src/maxson_build_utils/scaffold/logging_setup.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject


# -----
# Template
# -----

LOGGING_SETUP_TEMPLATE = Template(
    '''\
# src/$import_name/logging_setup.py

from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from .context import APP_NAME, LOG_FILE_PATH


# -----
# Constants
# -----

FILE_LOG_LEVEL = logging.DEBUG
FILE_LOG_MAX_BYTES = 5 * 1024 * 1024
FILE_LOG_BACKUP_COUNT = 3


# -----
# Logger
# -----

def get_logger() -> logging.Logger:
    """Return the application's package logger."""
    return logging.getLogger("$import_name")


# -----
# Formatters
# -----

def _file_formatter() -> logging.Formatter:
    """Return the formatter used for persistent file logging."""
    return logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _console_formatter(
    debug: bool = False,
    verbose: bool = False,
) -> logging.Formatter:
    """Return the formatter used for console logging."""
    if debug:
        fmt = "%(levelname)-7s %(message)s"
    elif verbose:
        fmt = "%(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    return logging.Formatter(fmt)


# -----
# File logging
# -----

def setup_file_logging() -> logging.Handler:
    """Create the persistent application log handler."""
    log_path = Path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=FILE_LOG_MAX_BYTES,
        backupCount=FILE_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(FILE_LOG_LEVEL)
    handler.setFormatter(_file_formatter())

    return handler


def _has_file_handler(logger: logging.Logger) -> bool:
    """Return whether the logger already has a file handler."""
    return any(
        isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )


# -----
# Application logging
# -----

def configure_logging_for_application(
    debug: bool = False,
    verbose: bool = False,
) -> None:
    """Configure logging for an application.

    The application owns its handlers.

    Persistent file logging always records DEBUG and above. Console logging
    is WARNING by default, INFO with verbose mode, and DEBUG with debug mode.
    """
    logger = get_logger()

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Reconfigure handlers so repeated calls do not produce duplicates.
    logger.handlers.clear()

    # Persistent file logging.
    file_handler = setup_file_logging()
    logger.addHandler(file_handler)

    # Console logging.
    if debug:
        console_level = logging.DEBUG
    elif verbose:
        console_level = logging.INFO
    else:
        console_level = logging.WARNING

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        _console_formatter(
            debug=debug,
            verbose=verbose,
        )
    )
    logger.addHandler(console_handler)

    logger.debug(
        "Application logging configured for %s.",
        APP_NAME,
    )


# -----
# Library logging
# -----

def configure_logging_for_library(
    debug: bool = False,
    verbose: bool = False,
) -> None:
    """Configure logging when this package is used as a library.

    Libraries do not own the host application's handlers. Messages propagate
    to the host application's logging configuration.
    """
    logger = get_logger()

    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)
    logger.propagate = True


# -----
# Traceback helpers
# -----

def log_traceback(logger: logging.Logger) -> None:
    """Print the current traceback when debug logging is enabled."""
    if logger.isEnabledFor(logging.DEBUG):
        traceback.print_exc(file=sys.stderr)
'''
)


# -----
# Rendering
# -----

def render_logging_setup_py(import_name: str) -> str:
    """Render the standard logging_setup.py content."""
    return LOGGING_SETUP_TEMPLATE.substitute(
        import_name=import_name,
    )


# -----
# Scaffold entry point
# -----

def run_init_logging_setup(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Scaffold logging_setup.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)

    target_path = pyproject.src_dir / "logging_setup.py"

    text = render_logging_setup_py(
        import_name=pyproject.import_name,
    )

    return write_str_to_file(
        target_path,
        text=text,
        overwrite=overwrite,
    )
