# src/dworshak_prompt/console_prompt_typer.py
"""
Typer-based console prompt. Non ideal for tty.
"""
from __future__ import annotations
import typer # keep at the top to enable failure, to hit the std lib fallback
from rich.console import Console
import sys
import logging
logger = logging.getLogger(__name__)

# Create a console that specifically targets stderr
stderr_console = Console(stderr=True)

from .keyboard_interrupt import PromptCancelled

def console_get_input_typer(
    message: str, 
    suggestion: str | None = None, 
    hide_input: bool = False,
    #default: str | None = None,
    ) -> str | None:
    try:        
            
        if hide_input:
            if suggestion:
                # Security notice: we don't pass the suggestion to the prompt,
                # so the user cannot "blindly" accept it by hitting Enter.
                logger.debug("Credential suggestion not shown in console for security. Use PromptMode.WEB or PromptMode.GUI to enjoy suggestion autofill for credentials.")
            hidden_msg = f"{message} (input hidden)"

            try:
                from rich.prompt import Prompt
                logger.debug("(try to) Use Prompt.ask() as the console_get_input_typer() solution. [hidden input]")
                return Prompt.ask(hidden_msg,
                                  password=True,
                                  console=stderr_console)
            except ImportError:
                logger.debug("Use typer.prompt() as the console_get_input_typer() solution. [hidden input]")
                return typer.prompt(hidden_msg, hide_input=True)
        
        # Standard credential case
        if suggestion: # and not hide_input
            logger.debug("Use typer.prompt() as the console_get_input_typer() solution. [suggestion]")
            return typer.prompt(
                message,
                default=suggestion)
        logger.debug("Use typer.prompt() as the console_get_input_typer() solution. []")
        return typer.prompt(message)
    except (typer.Abort, KeyboardInterrupt, EOFError, SystemExit):
        # We catch everything Typer/Rich/Python throws on Ctrl+C
        # and raise our own "Hard Stop" signal.
        raise PromptCancelled()
