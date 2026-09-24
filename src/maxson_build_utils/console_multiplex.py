# src/maxson_build_utils/console_multiplex.py

# move this to a dedicated library, or maybe it can be carried in blindwindow itself, but thats a lot of fallow code to lug around.
# libraries just to import and check other libraries, nice 
# Basically if you forget to add an extra your stuff will still work

from __future__ import annotations
from enum import Enum
from pathlib import Path
import sys
import pyhabitat

CONSOLE = get_console_multiplexed(force=None, avoid=None, order=None)

def _console_multiplex_check(
    force: ConsoleMultiplex | None = None, # single
    avoid: set[ConsoleMultiplex] None = None, # set
    order: list[ConsoleMultiplex] None = None, # ordered list
):
    try:
        from blindwindow.core import Console
        return ConsoleMultiplex.BW
    except ImportError:
        try:
            from rich.console import Console
            return ConsoleMultiplex.RICH
        except ImportError:
            return ConsoleMultiplex.NONE

class ConsoleMultiplex(str, Enum):
    RICH = "rich"
    BW = "blindwindow"
    NONE = "none"

def _get_consoles_by_console_multiplex(console_multiplex: ConsoleMultiplex=ConsoleMultiplex.NONE )->tuple[Console,Console]: # all types are rich.console.Console, but we should probabky have a dummy type in case the rich import fails? or that would defeat thw purpose of type checking. mayne rich should be required, unless there is a non-rich Console, but that might be beyond the bounds of this design, which relies in rich.
    """ Return console_stderr and console_stdout in tuple"""
    if console_multiplex == ConsoleMultiplex.RICH:
        from rich.console import Console
        console_stderr = Console(stderr=True)
        console_stdout = Console(stderr=False)
    elif console_multiplex == ConsoleMultiplex.BW:
        from blindwindow.core import Console
        console_stderr = Console(stderr=True, tee_sys=True)
        console_stdout = Console(stderr=False, tee_sys=True)
    elif console_multiplex == ConsoleMultiplex.NONE:
        console_stderr = None
        console_stdout = None
    else:
        console_stderr = None
        console_stdout = None
    return console_stderr, console_stdout

def get_consoles(
    force: ConsoleMultiplex | None = None, # single
    avoid: set[ConsoleMultiplex] = {}, # set
    order: list[ConsoleMultiplex] = [], # ordered list
)->tuple[Console,Console]: # matching signatures with _console_multiplex_check() is brittle?
    console_multiplex = _console_multiplex_check(
        force = force,
        avoid = avoid,
        order = order,
    )
    return _get_consoles_by_console_multiplex(console_multiplex)

def demo():
    from .console import ConsoleMultiplex, get_consoles
    console_stderr, console_stdout = get_consoles()
