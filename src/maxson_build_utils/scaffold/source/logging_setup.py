# src/maxson_build_utils/scaffold/logging_setup.py

from __future__ import annotations

from pathlib import Path
from string import Template

from ..helpers import write_str_to_file, WriteResult
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
from pathlib import Path

from .context import APP_NAME, LOG_FILE_PATH


# -----
# Constants
# -----

FILE_LOG_LEVEL = logging.DEBUG
FILE_LOG_MAX_BYTES = 5 * 1024 * 1024
FILE_LOG_BACKUP_COUNT = 3


# -----
# Logger Access
# -----

def get_logger(name: str | None = None) -> logging.Logger:
    """Return the package logger or a sub-logger under its namespace."""
    target_name = name or "$import_name"
    return logging.getLogger(target_name)


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
    """Return the formatter used for console output."""
    if debug:
        fmt = "%(levelname)-7s %(message)s"
    elif verbose:
        fmt = "%(message)s"
    else:
        fmt = "%(levelname)s: %(message)s"

    return logging.Formatter(fmt)


# -----
# Handlers
# -----

def setup_file_logging() -> logging.Handler | None:
    """Create the persistent application log handler safely."""
    if LOG_FILE_PATH is None:
        return None

    try:
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
    except (OSError, PermissionError) as err:
        sys.stderr.write(f"Warning: Failed to initialize file log at {LOG_FILE_PATH}: {err}\\n")
        return None


# -----
# Configurations
# -----

def configure_logging_for_application(
    debug: bool = False,
    verbose: bool = False,
    log_to_file: bool = True,
) -> logging.Logger:
    """Configure logging for an executable application entrypoint."""
    logger = get_logger()

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    # File Logging
    if log_to_file:
        file_handler = setup_file_logging()
        if file_handler is not None:
            logger.addHandler(file_handler)

    # Console Logging
    if debug:
        console_level = logging.DEBUG
    elif verbose:
        console_level = logging.INFO
    else:
        console_level = logging.WARNING

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        _console_formatter(debug=debug, verbose=verbose)
    )
    logger.addHandler(console_handler)

    logger.debug("Application logging configured for %s.", APP_NAME)
    return logger


def configure_logging_for_library(
    debug: bool = False,
    verbose: bool = False,
) -> logging.Logger:
    """Configure logging when this package is consumed as a library module."""
    logger = get_logger()

    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)
    logger.propagate = True

    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger


def configure_logging_all_debug() -> None:
    """Force DEBUG level logging globally across the root logger and third-party tools."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)-7s - [%(name)s] %(message)s")
    )
    root_logger.addHandler(console_handler)


# -----
# Diagnostics
# -----

def log_traceback(logger_instance: logging.Logger | None = None) -> None:
    """Safely print stack traces to stderr if debug level is active."""
    target = logger_instance or get_logger()
    if target.isEnabledFor(logging.DEBUG):
        traceback.print_exc(file=sys.stderr)
'''
)


# -----
# Rendering & Execution
# -----

def render_logging_setup_py(import_name: str) -> str:
    """Render the standard logging_setup.py template string."""
    return LOGGING_SETUP_TEMPLATE.substitute(
        import_name=import_name,
    )


def run_init_logging_setup(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Scaffold logging_setup.py inside src/<import_name>/."""
    pyproject = MaxsonPyProject(root_dir)

    if pyproject.src_dir is None:
        raise ValueError("Could not determine src directory for project initialization.")

    target_path = pyproject.src_dir / "logging_setup.py"

    text = render_logging_setup_py(
        import_name=pyproject.import_name or "app",
    )

    return write_str_to_file(
        target_path,
        text=text,
        overwrite=overwrite,
    )
