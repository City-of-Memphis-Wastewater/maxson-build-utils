# src/dworshak_prompt/gui_helpers.py
import logging
import platform
import pyhabitat
logger=logging.getLogger(__name__)
def get_tkinter_hint() -> str:
    os_name = platform.system().lower()
    hint_base = (
        "GUI mode skipped: Tkinter unavailable.\n"
        "Tkinter is Python's standard GUI library, but it may need installation or configuration.\n"
        "Common fixes:\n"
    )

    if "darwin" in os_name:  # macOS
        return hint_base + (
            "• On macOS: Install via Homebrew (brew install python-tk) or your Python installer (e.g., python.org download with Tkinter option).\n"
            "• Ensure your Python is built with Tcl/Tk support: python -m tkinter (should open a window).\n"
            "More: https://docs.python.org/3/library/tkinter.html#installing-tk"
        )

    elif "linux" in os_name:
        if pyhabitat.on_termux():
            return hint_base + (
                "• In Termux: Install python-tkinter (pkg install python-tkinter ).\n"
                "• For GUI support, set up X11 forwarding (https://wiki.termux.com/wiki/Graphical_Environment).\n"
                "More: https://wiki.termux.com/wiki/Python"
            )
        elif pyhabitat.on_wsl():  # WSL-specific
            return hint_base + (
                "• In WSL: Install python3-tk (sudo apt install python3-tk for Ubuntu/Debian).\n"
                "• For GUI support, enable WSLg (Windows 11+ WSL) or set up X11 forwarding (e.g., Xming or VcXsrv on Windows).\n"
                "• Test: python3 -m tkinter (should open a window).\n"
                "More: https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps"
            )
        else:  # General Linux
            return hint_base + (
                "• On Linux: Install via your package manager (e.g., sudo apt install python3-tk on Ubuntu/Debian, or sudo dnf install python3-tkinter on Fedora).\n"
                "• Test: python3 -m tkinter (should open a window).\n"
                "More: https://docs.python.org/3/library/tkinter.html#installing-tk"
            )

    elif "windows" in os_name:
        return hint_base + (
            "• On Windows: Tkinter is usually bundled with Python installers from python.org (check 'tcl/tk and IDLE' option).\n"
            "• If missing, reinstall Python with the option enabled.\n"
            "• Test: python -m tkinter (should open a window).\n"
            "More: https://docs.python.org/3/library/tkinter.html#installing-tk"
        )

    else:  # Generic fallback
        return hint_base + (
            "• Install Tkinter via your Python distribution or package manager.\n"
            "• Test: python -m tkinter (should open a window).\n"
            "More: https://docs.python.org/3/library/tkinter.html#installing-tk"
        )

def init_x11_threads():
    """Ensures X11 is initialized in thread-safe mode before any UI call."""
    import sys
    if sys.platform.startswith('linux'):
        import ctypes
        # Use find_library to ensure we get the right path
        from ctypes.util import find_library

    if sys.platform.startswith('linux'):
        try:
            lib_path = find_library('X11')
            if lib_path:
                x11 = ctypes.cdll.LoadLibrary(lib_path)
                # Attempt to initialize thread safety
                status = x11.XInitThreads()
                if status:
                    logger.debug(f"XInitThreads() succeeded (status: {status})")
                else:
                    logger.warning("XInitThreads() returned 0; might be too late.")
            else:
                logger.error("Could not locate X11 library.")
        except Exception as e:
            logger.debug(f"Failed to init X threads: {e}")
