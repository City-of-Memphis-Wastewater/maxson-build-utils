# src/pyhabitat/cli.py
from __future__ import annotations
import argparse
import inspect
import logging
from pathlib import Path
import sys
import typing


import pyhabitat
from ._version import __version__
from .logging_setup import configure_logging

logger = logging.getLogger(__name__)


def run_cli() -> None:
    """Parse CLI arguments using subparsers for an elegant, scalable tool."""
    current_version = __version__
    
    # Root parser
    parser = argparse.ArgumentParser(
        description="PyHabitat: Python environment and build introspection"
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'PyHabitat {current_version}'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help="Enable global verbose debug logging"
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help="Enable informative status logging"
    )

    parser.add_argument(
        "--clear-cache",
        action='store_true',
        help="Force fresh environment checks with cached results.",
    )

    # Subparsers for independent commands
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="command",
        help="Target function or routine to run"
    )

    # 1. Register a dedicated subparser for the default full system report
    report_parser = subparsers.add_parser("report", help="Run the full pyhabitat environment report (default)")
    report_parser.add_argument("--path", type=str, default=None, help="Path to inspect (defaults to sys.argv[0])")

    # 2. Dynamically loop through __all__ and map functions to CLI sub-commands
    for name in pyhabitat.__all__:
        if name in ("__version__", "report", "safe_notify"):
            continue
            
        func = getattr(pyhabitat, name, None)
        type_hints = typing.get_type_hints(func)

        if not callable(func):
            continue

        # Create a subcommand matching the exact function name
        doc = func.__doc__ or f"Run pyhabitat.{name}()"
        first_line_doc = doc.strip().split("\n")[0]
        cmd_parser = subparsers.add_parser(name, help=first_line_doc)

        # Inspect the function signature to add targeted parameters automatically
        # ---
        try:
            sig = inspect.signature(func)

            for name, param in sig.parameters.items():

                # skip debug and info arga because they exist as base command flags
                if name in {"debug", "info"}:
                    continue

                arg = f"--{name.replace('_', '-')}"

                kwargs = {
                    "dest": name,
                }

                annotation = type_hints.get(name, str)
                if annotation is bool:
                    kwargs["action"] = argparse.BooleanOptionalAction
                if annotation is Path:
                    kwargs["type"] = Path
                elif annotation in (int, float, str):
                    kwargs["type"] = annotation
                else:
                    kwargs["type"] = str

                # ---
                '''
                kwargs = {
                    "dest": name,
                    "type": str,
                }

                if param.default is inspect.Parameter.empty:
                    kwargs["required"] = True
                else:
                    kwargs["default"] = param.default
                '''
                cmd_parser.add_argument(arg, **kwargs)

        # ---
        except (ValueError, TypeError):
            logger.warning("Cannot inspect %s", func)
            continue
        
    # Intercept --clear-cache before parsing so it bypasses required subcommands
    if "--clear-cache" in sys.argv:
        if hasattr(pyhabitat, "clear_mpl_cache"):
            pyhabitat.clear_mpl_cache()
        if hasattr(pyhabitat, "clear_shell_cache"):
            pyhabitat.clear_shell_cache()
        pyhabitat.safe_notify("All cached results cleared to allow for fresh checks.")
        return

    # Handle the empty arguments edge-case by falling back to the standard report
    if len(sys.argv) == 1:
        pyhabitat.report(path=None, debug=False)
        return

    args = parser.parse_args()
    # Initialize the zero-dep logging setup
    from .logging_setup import configure_logging
    configure_logging(debug=args.debug, info=args.info)

    # Execution logic branch
    if args.command == "report":
        report_path = Path(args.path) if args.path else None
        pyhabitat.report(path=report_path, debug=args.debug)
        return
    # ---
    '''
    if args.command:
        func = getattr(pyhabitat, args.command)
        kwargs = {}
        
        # Build kwargs based on what the parsed subcommand provides
        try:
            sig = inspect.signature(func)
            params = sig.parameters
        except (ValueError, TypeError):
            params = {}

        if hasattr(args, "path") and args.path:
            resolved_path = Path(args.path)
            if "path" in params:
                kwargs["path"] = resolved_path
            elif "exec_path" in params:
                kwargs["exec_path"] = resolved_path

        # Trap missing mandatory path argument validations cleanly
        else:
            for p_name in ("path", "exec_path"):
                if p_name in params and params[p_name].default == inspect.Parameter.empty:
                    pyhabitat.safe_notify(
                        f"Error: Command '{args.command}' requires a target path parameter. "
                        f"Provide one using '--path <target_path>'."
                    )
                    sys.exit(1)
            
        if hasattr(args, "debug") and args.debug and "debug" in params:
            kwargs["debug"] = True
        # ---
        
        try:
            result = func(**kwargs)
            if result is not None:
                #print(result)
                # Format attributes cleaner if someone inspects a structured SystemInfo object
                if hasattr(result, "__dict__") and not isinstance(result, (str, bool, int, dict, list)):
                    import pprint
                    pprint.pprint(result.__dict__)
                else:
                    print(result)
        except Exception as e:
            pyhabitat.safe_notify(f"Error executing '{args.command}': {e}")


        # ---
    '''
    if args.command:
        func = getattr(pyhabitat, args.command)

        try:
            sig = inspect.signature(func)
            params = sig.parameters
        except (ValueError, TypeError):
            params = {}

        kwargs = {}

        # Copy parsed CLI arguments into function arguments
        for name, param in params.items():
            if hasattr(args, name):
                value = getattr(args, name)

                if value is None:
                    continue

                # Convert path-like arguments back to Path objects
                if name in {"path", "exec_path"}:
                    value = Path(value)

                kwargs[name] = value

        try:
            result = func(**kwargs)

            if result is not None:
                if hasattr(result, "__dict__") and not isinstance(
                    result, (str, bool, int, dict, list)
                ):
                    import pprint
                    pprint.pprint(result.__dict__)
                else:
                    print(result)

        except Exception as e:
            pyhabitat.safe_notify(
                f"Error executing '{args.command}': {e}"
            )
