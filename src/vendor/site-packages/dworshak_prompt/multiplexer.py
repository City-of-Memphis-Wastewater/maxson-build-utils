# src/dworshak_prompt/multiplexer.py
from __future__ import annotations
import pyhabitat as ph
from typing import Set, Any
import threading
import traceback
import sys
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .gui_helpers import get_tkinter_hint
if ph.tkinter_is_available():
    from .gui_prompt import gui_get_input
else:
    gui_get_input = None
from .web_prompt import browser_get_input
from .keyboard_interrupt import PromptCancelled
from .server import stop_prompt_server
from .prompt_manager_web import PromptManagerWeb
from .helpers import (
        PromptMode, 
        InterruptBehavior,
        resolve_str_to_list, 
        resolve_str_to_set
        )
from .environment import has_real_tty, get_console_provider, is_likely_ci_or_non_interactive, interactive_terminal_is_available

class DworshakPrompt: 
    def __init__(self,
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None =None,
        interrupt_behavior: InterruptBehavior = InterruptBehavior.RETURN_NONE,
    ):
        self.interface_priority = interface_priority
        self.interface_avoid = interface_avoid
        self.interrupt_behavior = interrupt_behavior
        
    def ask(
        self,
        message: str = "Enter value",
        suggestion: str | None = None,
        default: Any | None = None,
        hide_input: bool = False, 
        interface_priority: list[PromptMode] | None = None,
        interface_avoid: set[PromptMode] | None = None,
        interrupt_event: threading.Event | None = None,
        timeout: int | float | None = None,
        interrupt_behavior: InterruptBehavior | None = None
    ) -> str | None:
        import logging
        logger = logging.getLogger(__name__)
        #from .logging_setup import setup_logging
        #logger = setup_logging(verbose=logging.INFO, debug=logging.DEBUG, initial=True)

        if interface_priority is None:
            interface_priority = self.interface_priority
        if interface_avoid is None:
            interface_avoid = self.interface_avoid

        # Use existing interrupt_event or create a local one for this call
        if interrupt_event is None:
            interrupt_event = threading.Event()

        if interrupt_behavior is None:
            interrupt_behavior = self.interrupt_behavior

        '''

        # CI/Headless Detection
        # If we aren't forceing TTY and aren't on a system that can spawn a GUI/Web window,
        # return the default immediately to mitigate a potential Dworshak failure mode in CI.
        if is_likely_ci_or_non_interactive() and os.environ.get("DWORSHAK_FORCE_INTERACTIVE_TTY") != "1":
            logger.debug("CI environment. Returning default to avoid blocking.")
            return default
        
        # TTY detection
        # If we aren't in a TTY.
        # return the default immediately to mitigate a potential Dworshak failure mode in CI.
        # use DWORSHAK_FORCE_INTERACTIVE_TTY=1 when wrapping prompt calls
        # like: DWORSHAK_FORCE_INTERACTIVE_TTY=1 VAR=$(dworshak-prompt ask)
        if not has_real_tty():
            logger.debug("No interactive terminal; checking GUI/Web availability.")
            

        #if not interactive_terminal_is_available() or \
        if not has_real_tty() and \
        not ph.tkinter_is_available() or \
        not ph.web_browser_is_available(): # Hypothetical pyhabitat check
            logger.debug("Non-interactive environment detected. Default value assigned.")
            return default
        '''
        
        # Force interactive check
        logger.debug(f"{os.environ.get('DWORSHAK_FORCE_INTERACTIVE_TTY')=}")
        forced_tty = os.environ.get("DWORSHAK_FORCE_INTERACTIVE_TTY") == "1"
        logger.debug(f"{forced_tty=}")
        logger.debug(f"{os.path.exists('/dev/tty')=}")

        # Early Exit check
        if not forced_tty:
            if is_likely_ci_or_non_interactive():
                logger.debug("CI environment. Returning default.")
                return default

            # If NO path to user exists at all
            if not (interactive_terminal_is_available() or 
                    ph.tkinter_is_available() or 
                    ph.web_browser_is_available() or 
                    os.path.exists("/dev/tty")):
                logger.debug("Non-interactive environment detected.")
                return default

        interface_avoid = interface_avoid or set()
        interface_avoid = resolve_str_to_set(interface_avoid)
        interface_priority = resolve_str_to_list(interface_priority)

        avoid_tk_on_wsl = _check_avoid_tkinter_on_wsl(interface_priority,logger)

        if avoid_tk_on_wsl:
            interface_avoid.add(PromptMode.GUI)

        default_order = [PromptMode.CLI, PromptMode.GUI, PromptMode.WEB]
        if interface_priority:
            # User choice first, followed by everything else as a safety net
            effective_interface_priority = interface_priority + [m for m in default_order if m not in interface_priority]
        else:
            effective_interface_priority = default_order

        if timeout:
            # A background timer to fire the interrupt signal
            timer = threading.Timer(timeout, lambda: interrupt_event.set())
            timer.start()

        for interface_mode in effective_interface_priority:
            if interface_mode in interface_avoid:
                logger.debug(f"Skipping {interface_mode} (avoided)")
                continue

            logger.debug(f"\n=== Interface Mode: {interface_mode} ===")
            
            try:
                if interface_mode == PromptMode.CLI:
                    # if not has_real_tty():
                    if not interactive_terminal_is_available() and not forced_tty:
                        logger.debug(f"{interface_mode} skipped: No interactive terminal.")
                        continue
                    
                    def reject_suggestion_for_hidden_inputs(suggestion: str | None, hide_input: bool) -> str | None:
                        if suggestion and hide_input:
                            logger.warning(f"A suggestion cannot be accepted in the console while the input is hidden. Simply pressing enter will submit an empty string, not the suggestion. Use the WEB or GUI interfaces to see a suggestion securely. \n\nRecommendation 1: Do no use suggestions for secrets. \nRecommendation 2: Keep suggestions for secrets out of your console history and out of your public codebases.")
                            logger.info(f"Use PromptMode.WEB or PromptMode.GUI to enjoy suggestions for hidden credentials.")
                        if hide_input:
                            return None  # Suggestion is completely blocked from hidden prompts
                        return suggestion

                    console_get_input = get_console_provider()
                    suggestion = reject_suggestion_for_hidden_inputs(suggestion, hide_input)
                    val = console_get_input(message = message, suggestion = suggestion, hide_input = hide_input)
                    log_val = "'********'" if hide_input else repr(val)
                    logger.debug(f"SUCCESS: {interface_mode} returned: {log_val}")
                    return val

                elif interface_mode == PromptMode.GUI:
                    #logger.warning(f"ph.tkinter_is_available() = {ph.tkinter_is_available()}")
                    if not ph.tkinter_is_available():
                        logger.warning(f"{interface_mode} skipped: Tkinter unavailable.")
                        logger.debug(get_tkinter_hint())  
                        continue

                        
                    val = gui_get_input(message = message, suggestion = suggestion, hide_input = hide_input)
                    if val is not None:
                        log_val = "'********'" if hide_input else repr(val)
                        logger.debug(f"SUCCESS: {interface_mode} returned: {log_val}")
                        return val
                    
                    logger.debug(f"GUI cancelled. Raising PromptCancelled.")
                    raise PromptCancelled()

                elif interface_mode == PromptMode.WEB:
                    local_manager = PromptManagerWeb()
                    try:
                        val = browser_get_input(
                            message, 
                            suggestion, 
                            hide_input, 
                            manager = local_manager, 
                            stop_event = interrupt_event
                            )
                        if val is not None:
                            log_val = "'********'" if hide_input else repr(val)
                            logger.debug(f"SUCCESS: {interface_mode} returned: {log_val}")
                            return val
                        logger.debug(f"WEB returned None. Raising PromptCancelled.")
                        raise PromptCancelled()
                    finally:
                        stop_prompt_server()

            
            except BaseException as e:
                exc_type = type(e)
                exc_name = exc_type.__name__
                exc_module = exc_type.__module__
                
                logger.debug(f"!!! EXCEPTION TRIGGERED !!!")
                logger.debug(f"Class Name: {exc_name}")
                logger.debug(f"Full Path:  {exc_module}.{exc_name}")
                logger.debug(f"Exception Type: {exc_name}")
                # MASKING LOGIC to prevent secret value leaks
                if hide_input:
                    logger.debug("Repr:       <Masked due to hide_input=True>")
                    logger.debug("Args:       <Masked>")
                else:
                    logger.debug(f"Repr:       {repr(e)}")
                    logger.debug(f"Args:       {e.args}")

                stop_signals = {"KeyboardInterrupt", "Abort", "SystemExit", "EOFError", "PromptCancelled"}
                
                if exc_name in stop_signals or isinstance(e, (KeyboardInterrupt, PromptCancelled)):
                    logger.debug(f">>> MATCHED STOP SIGNAL: {exc_name}. EXITING FUNCTION.")
                    if interrupt_event:
                        interrupt_event.set()

                    if interrupt_behavior == InterruptBehavior.EXIT:
                        print("\n[!] Operation cancelled by user.", file=sys.stderr)
                        sys.exit(130)
                    elif interrupt_behavior == InterruptBehavior.RAISE:
                        raise PromptCancelled()
                    elif interrupt_behavior == InterruptBehavior.RETURN_DEFAULT:
                        return default
                    elif interrupt_behavior == InterruptBehavior.RETURN_NONE:
                        return None

                # For technical failures, we log the traceback at DEBUG level
                logger.debug(f">>> TECHNICAL FAILURE detected. Investigating traceback...")
                if logger.isEnabledFor(logging.DEBUG):
                    traceback.print_exc(file=sys.stdout)

                logger.debug(f"Continuing to fallback interface mode...")
                continue

            logger.debug("All interface modes exhausted.")
            raise RuntimeError("No input method succeeded.")
        

def dworshak_ask(message: str | None = None, suggestion: str | None = None, **kwargs):
    """
    Passes arguments to DworshakPrompt().ask().
    If message/suggestion are None, DworshakPrompt defines the defaults.
    """
    return DworshakPrompt().ask(
        message=message, 
        suggestion=suggestion, 
        **kwargs
    )

# --- helpers ---

def _check_avoid_tkinter_on_wsl(interface_priority,logger)->bool:
    if PromptMode.GUI in interface_priority:
        warn=True
    else:
        warn=False
        
    if ph.on_wsl():
        raw_val = os.getenv("DWORSHAK_TRY_TKINTER_ON_WSL")
        logger.debug(f"raw DWORSHAK_TRY_TKINTER_ON_WSL = {raw_val!r}")
        
        # Convert common truthy strings to boolean
        if raw_val is not None:
            dworshak_try_tkinter_on_wsl = raw_val.lower() in ('1', 'true', 'yes', 'on', 'enable')
        else:
            dworshak_try_tkinter_on_wsl = False
        
        logger.debug(f"DWORSHAK_TRY_TKINTER_ON_WSL interpreted as {dworshak_try_tkinter_on_wsl}")
        instruction_to_allow_tk_on_wsl=f"PromptMode.GUI avoided for WSL; to try it, set `export DWORSHAK_TRY_TKINTER_ON_WSL=1`"
        if not dworshak_try_tkinter_on_wsl:
            if warn:
                logger.debug(instruction_to_allow_tk_on_wsl)
            else:
                logger.debug(instruction_to_allow_tk_on_wsl)
            return True
        else:
            return False
        
# --- Demo entry ---

def main():
    DworshakPrompt().ask(
        "What is your name?",
        suggestion="George"
    )
