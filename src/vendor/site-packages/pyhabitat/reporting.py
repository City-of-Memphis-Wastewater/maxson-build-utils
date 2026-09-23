# src/pyhabitat/report.py 
from __future__ import annotations  
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def should_pause():
    import pyhabitat as ph
    if ph.in_repl():
        return False

    if sys.flags.interactive:
        return False

    if not sys.stdin or not sys.stdin.isatty():
        return False

    if not sys.stdout or not sys.stdout.isatty():
        return False

    return True
    
def report(path=None, debug=False):
    """Print a comprehensive environment report.

    Args:
        path (Path | str | None): Path to inspect (defaults to sys.argv[0]).
        debug (bool): Enable verbose debug output.
    """
    import pyhabitat as ph
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)  # Suppress matplotlib debug logs
    print("================================")
    print("======= PyHabitat Report =======")
    print("================================")
    print("\nCurrent Build Checks ")
    print("# // Based on hasattr(sys,..) and getattr(sys,..)")
    print("------------------------------")
    print(f"in_repl(): {ph.in_repl()}")
    print(f"as_frozen(): {ph.as_frozen()}")
    print(f"as_pyinstaller(): {ph.as_pyinstaller()}")
    print("\nOperating System Checks")
    print("# // Based on platform.system()")
    print("------------------------------")
    print(f"on_windows(): {ph.on_windows()}")
    print(f"on_macos(): {ph.on_macos()}")
    print(f"on_linux(): {ph.on_linux()}")
    print(f"on_wsl(): {ph.on_wsl()}")
    print(f"on_android(): {ph.on_android()}")
    print(f"on_termux(): {ph.on_termux()}")
    print(f"on_pydroid(): {ph.on_pydroid()}")
    print(f"on_ish_alpine(): {ph.on_ish_alpine()}")
    print(f"on_freebsd(): {ph.on_freebsd()}")
    print(f"on_chromeos_crostini(): {ph.on_chromeos_crostini()}")
    print("\nCapability Checks")
    print("-------------------------")
    print(f"tkinter_is_available(): {ph.tkinter_is_available()}")
    print(f"matplotlib_is_available_for_gui_plotting(): {ph.matplotlib_is_available_for_gui_plotting()}")
    print(f"matplotlib_is_available_for_headless_image_export(): {ph.matplotlib_is_available_for_headless_image_export()}")
    print(f"web_browser_is_available(): {ph.web_browser_is_available()}")
    print(f"interactive_terminal_is_available(): {ph.interactive_terminal_is_available()}")
    print("\nInterpreter Checks")
    print("# // Based on sys.executable()")
    print("-----------------------------")
    print(f"interp_path(): {ph.interp_path()}")
    if debug:
        # Do these debug prints once to avoid redundant prints
        # Supress redundant prints explicity using suppress_debug=True, 
        # so that only unique information gets printed for each check, 
        # even when more than one use the same functions which include debugging logs.
        #print(f"ph.check_executable_path(ph.interp_path(), debug=True)")
        ph.check_executable_path(ph.interp_path(), debug=debug)    
        #print(f"read_magic_bites(ph.interp_path(), debug=True)")
        ph.read_magic_bytes(ph.interp_path(), debug=debug)
    print(f"is_elf(ph.interp_path()): {ph.is_elf(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print(f"is_windows_portable_executable(ph.interp_path()): {ph.is_windows_portable_executable(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print(f"is_macos_executable(ph.interp_path()): {ph.is_macos_executable(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print(f"is_pyz(ph.interp_path()): {ph.is_pyz(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print(f"is_pipx(ph.interp_path()): {ph.is_pipx(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print(f"is_python_script(ph.interp_path()): {ph.is_python_script(ph.interp_path(), debug=debug, suppress_debug=True)}")
    print("\nCurrent Environment Check")
    print("# // Based on sys.argv[0]")
    print("-----------------------------")
    inspect_path = path if path is not None else (None if sys.argv[0] == '-c' else sys.argv[0])
    logging.debug(f"Inspecting path: {inspect_path}")
    # Early validation of path
    if path is not None:
        path_obj = Path(path)
        if not path_obj.is_file():
            print(f"Error: '{path}' is not a valid file or does not exist.")
            if debug:
                logging.error(f"Invalid path: '{path}' is not a file or does not exist.")
            raise SystemExit(1)
    script_path = None
    if path or (sys.argv[0] and sys.argv[0] != '-c'):
        script_path = Path(path or sys.argv[0]).resolve()
    print(f"sys.argv[0] = {str(sys.argv[0])}")
    if script_path is not None:
        print(f"script_path = {script_path}")
        if debug:
            # Do these debug prints once to avoid redundant prints
            # Supress redundant prints explicity using suppress_debug=True, 
            # so that only unique information gets printed for each check, 
            # even when more than one use the same functions which include debugging logs.
            #print(f"check_executable_path(script_path, debug=True)")
            ph.check_executable_path(script_path, debug=debug)
            #print(f"read_magic_bites(script_path, debug=True)")
            ph.read_magic_bytes(script_path, debug=debug)
        print(f"is_elf(): {ph.is_elf(script_path, debug=debug, suppress_debug=True)}")
        print(f"is_windows_portable_executable(): {ph.is_windows_portable_executable(script_path, debug=debug, suppress_debug=True)}")
        print(f"is_macos_executable(): {ph.is_macos_executable(script_path, debug=debug, suppress_debug=True)}")
        print(f"is_pyz(): {ph.is_pyz(script_path, debug=debug, suppress_debug=True)}")
        print(f"is_pipx(): {ph.is_pipx(script_path, debug=debug, suppress_debug=True)}")
        print(f"is_python_script(): {ph.is_python_script(script_path, debug=debug, suppress_debug=True)}")
    else:
        print("Skipping: ") 
        print("    is_elf(), ")
        print("    is_windows_portable_executable(), ")
        print("    is_macos_executable(), ")
        print("    is_pyz(), ")
        print("    is_pipx(), ") 
        print("    is_python_script(), ")
        print("All False, script_path is None.")
    print("")
    print("=================================")
    print("=== PyHabitat Report Complete ===")
    print("=================================")
    print("")
    if should_pause():
        print("Press Return to Continue...", file=sys.stderr)
        sys.stdin.readline()
    '''
    interactive = ph.in_repl() or sys.flags.interactive
    if not interactive:
        # Keep window open.
        try:
            print("Press Return to Continue...", file=sys.stderr)
            sys.stdin.readline() # does not use eval() under the hood, reduce security concern
            #input("Press Return to Continue...")
        except Exception as e:
            logging.debug("input() failed")
    '''
