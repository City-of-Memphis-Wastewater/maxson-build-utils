# src/pyhabitat/gui_elements.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
import io
import importlib.util
from enum import Enum, auto

# Backport functools.cache for Python < 3.9
from ._compat import cache
from .environment import on_termux, on_linux

# On Windows, we need the msvcrt module for non-blocking I/O
#try:
#    import msvcrt
#except ImportError:
#    msvcrt = None

__all__ = [
    'matplotlib_is_available_for_gui_plotting',
    'matplotlib_is_available_for_headless_image_export',
    'tkinter_is_available',
    'web_browser_is_available',
    'AppMode',
    'probe_app_mode_mgu',
]

class AppMode(Enum):
    GUI = auto()
    CLI = auto()
    TK_GUI = auto()
    TYPER_CLI = auto()

def clear_mpl_cache()->None:
    """Clear every @cache used in pyhabitat, and call from CLI using --clear-cache"""
    matplotlib_is_available_for_gui_plotting.cache_clear()
    matplotlib_is_available_for_headless_image_export.cache_clear()

# --- GUI CHECKS ---
@cache # alt to globals
def matplotlib_is_available_for_gui_plotting(termux_has_gui=False):
    """Check if Matplotlib is available AND can use a GUI backend for a popup window."""
    # 1. Termux exclusion check (assume no X11/GUI)
    # Exclude Termux UNLESS the user explicitly provides termux_has_gui=True.
    if on_termux() and not termux_has_gui: 
        return False
    
    # 2. Tkinter check (The most definitive check for a working display environment)
    # If tkinter can't open a window, Matplotlib's TkAgg backend will fail.
    if not tkinter_is_available():
        return False

    # 3. Matplotlib + TkAgg check
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        # Only switch to TkAgg is no interactive backend is already active.
        # At this point, we know tkinter is *available*.
        current_backend = matplotlib.get_backend().lower()
        if not current_backend or 'inline' in current_backend:
        #if current_backend in () or 'inline' in current_backend:
            # Non-interactive, safe to switch
            # 'TkAgg' is often the most reliable cross-platform test.
            matplotlib.use('TkAgg', force=True)
        else:
            # already using QtAgg, Gtk3Agg, etc.
            matplotlib.use(current_backend, force=True)
        
        # 'TkAgg' != 'Agg'. The Agg backend is for non-gui image export. 
        if matplotlib.get_backend().lower() != 'tkagg':
            matplotlib.use('TkAgg', force=True)
        
        # A simple test call to ensure the backend initializes
        # This final test catches any edge cases where tkinter is present but 
        # Matplotlib's *integration* with it is broken
        
        fig=plt.figure()
        plt.close(fig)

        return True

    except Exception:
        # Catches Matplotlib ImportError or any runtime error from the plt.figure() call
        return False
    
@cache
def matplotlib_is_available_for_headless_image_export():
    """Check if Matplotlib is available AND can use the Agg backend for image export."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        # The Agg backend (for PNG/JPEG export) is very basic and usually available 
        # if the core library is installed. We explicitly set it just in case.
        # 'Agg' != 'TkAgg'. The TkAgg backend is for interactive gui image display. 
        matplotlib.use('Agg', force=True) 
        
        # A simple test to ensure a figure can be generated
        fig = plt.figure()
        # Ensure it can save to an in-memory buffer (to avoid disk access issues)
        fig.savefig(io.BytesIO(), format='png')
        plt.close(fig)
        return True
        
    except Exception as e:
        return False
    finally:
        # guarantee no figures leak
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass

def tkinter_is_available() -> bool:
    """Check if tkinter is available and can successfully connect to a display."""

    # Quick exit: If no DISPLAY is set on Linux/WSL, GUI is impossible
    if on_linux() and not os.environ.get("DISPLAY"):
        return False
        
    try:
        import tkinter as tk
        
        # Perform the actual GUI backend test for absolute certainty.
        # This only runs once per script execution.
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.destroy()
        
        return True
    except Exception:
        # Fails if: tkinter module is missing OR the display backend is unavailable
        return False

def probe_app_mode_mgu(gui_pkg: str = "maxson_gui_utils") -> AppMode:
    """Determine runtime execution mode based on display capabilities and installed packages."""

    if not tkinter_is_available():
        return AppMode.CLI
    if importlib.util.find_spec(gui_pkg) is None:
        return AppMode.CLI
    return AppMode.GUI
