
#!/usr/bin/env python3
# src/maxson_build_utils/tk_gui.py
from __future__ import annotations
import pyhabitat
import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
from pathlib import Path
from typing import Optional
import ctypes
import sys
import maxson_gui_utils as mgu
from maxson_gui_utils.resources import resource_path
from maxson_gui_utils.tk_components.widgets import create_path_entry
from maxson_gui_utils.tk_utils import check_frame_geometry

try:
    from maxson_gui_utils.tk_utils import center_window_on_primary
except ImportError:
    center_window_on_primary = None
try:
    from maxson_gui_utils.external_web_launch import launch_configured_website
except ImportError:
    launch_configured_website = None

import logging

# --- Core Imports ---

from .context import CONFIG_PATH, APP_NAME, IMPORT_NAME, APP_DIR
from ._version import get_version, __version__
#from .paths import (
#            LOGO_FILENAME_PNG,
#            LOGO_FILENAME_ICO,
#            get_icon_path,
#            REPO_URL
#            )

logger=logging.getLogger(__name__)

APP_W = 100
APP_H = 100

# RedirectText
class GuiApp:

    # --- Lifecycle & Initialization ---

    def __init__(self, root: tk.Tk):
        self.root = root

        # Do NOT load theme yet.
        # Run the "heavy" initialization first
        self._initialize_vars()

        # --- Debug ---
        #logger.debug(f'patchlevel: {root.tk.call("info", "patchlevel")}')
        #logger.debug(f'package,Tcl: {root.tk.call("package", "present", "Tcl")}')
        #logger.debug(f'package,Tk: {root.tk.call("package", "present", "Tk")}')
        logger.debug(f'tcl_library: {root.tk.call("set", "tcl_library")}')
        # NOW load the theme (this takes ~100-300ms)
        self._initialize_forest_theme()

        # Apply the theme
        style = ttk.Style()
        style.configure(".", padding=2)                # global min padding
        style.configure("TFrame", padding=2)
        style.configure("TLabelFrame", padding=(4,2))
        style.configure("TButton", padding=4)
        style.configure("TCheckbutton", padding=2)
        style.configure("TRadiobutton", padding=2)
        style.theme_use("forest-dark")

        self.root.title(f"{APP_NAME} v{get_version()}")  # Short title
        self.root.geometry(f"{APP_W}x{APP_H}")  # Smaller starting size
        self.root.minsize(600, 50)    # Prevent too-small window

        self._set_icon()

        # --- 2. Widget Construction ---
        self._create_widgets()
        self._initialize_menubar()

    def _initialize_vars(self):
        """Build necessary tk variables."""
        self.entry_path = tk.StringVar(value="")
        

    # --- Theme & Visual Initialization ---
    def _initialize_forest_theme(self):
        theme_dir = resource_path("themes", "forest")
        self.root.tk.call("source", str(theme_dir / "forest-light.tcl"))
        self.root.tk.call("source", str(theme_dir / "forest-dark.tcl"))

    def _toggle_theme(self):
        style = ttk.Style(self.root) # Explicitly link style to our root
        if style.theme_use() == "forest-light":
            style.theme_use("forest-dark")
        elif style.theme_use() == "forest-dark":
            style.theme_use("forest-light")

    def _set_icon(self):
        try:
            png_path = None # get_icon_path(LOGO_FILENAME_PNG)
            if png_path.exists():
                self.icon_img = PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self.icon_img)
        except Exception:
            pass
        try:
            ico_path = None # get_icon_path(LOGO_FILENAME_ICO)
            if ico_path.exists():
                self.root.iconbitmap(str(ico_path))
        except Exception:
            pass


    def _initialize_menubar(self):
        """Builds the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=tools_menu)

        tools_menu.add_command(label="Show Application Directory ", command=lambda: self._show_app_dir_in_system_explorer())
        tools_menu.add_command(label="Launch Configured Website ", command=lambda: self._launch_configured_website())
        tools_menu.add_command(label="Launch BlindWindow ", command=lambda: self._launch_blindwindow())
        tools_menu.add_command(label="Serve Webapp", command=lambda: self._serve_webapp())
        
        #tools_menu.add_separator()
        #tools_menu.add_command(label="Readme", command=self._show_readme)

    def _show_readme(self):
        """Placeholder for the missing readme method."""
        messagebox.showinfo("Readme", "Readme utility.")

    # --- UI Component Building ---
    def _launch_configured_website(self):
        if launch_configured_website is not None:
            launch_configured_website(path=CONFIG_PATH)
        else:
            messagebox.showinfo(
                "Dependency",
                "maxson-gui-utils needs to be included in the venv to use this feature."
            )

    def _launch_blindwindow(self):
        from blindwindow.core import launch_blindwindow
        launch_blindwindow()

    def _serve_webapp(self):
        messagebox.showinfo(
            "Placeholder",
            "Link up your webapp entry point function here."
        )

    def _about_button(self):
        messagebox.showinfo(
            "About",
            "For help, please see Clayton Bennett."
        )
    def _create_widgets(self):
        """Compact layout with reduced padding."""

        # --- Control Frame (Top) ---
        control_frame = ttk.Frame(self.root, padding=(4, 2, 4, 2))
        #control_frame.pack(fill='x', pady=(2, 2))
        control_frame.pack(
            fill="both",
            expand=False,
            pady=(2, 2),
        )

        # Grid configuration
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)

        control_frame.grid_rowconfigure(0, weight=0)
        control_frame.grid_rowconfigure(1, weight=0)
        
        btn_open_browser_to_files = ttk.Button(control_frame, text="About", command=lambda: self._show_about(), width=8)
        btn_open_browser_to_files.grid(row=0, column=0, columnspan=1, pady=6, sticky='ew', padx=(0, 3))

        # === Action Buttons ===
        run_analysis_btn = ttk.Button(control_frame, text="▶ Run Main", command=self._run_main, style='Accent.TButton', width=16) #
        run_analysis_btn.grid(row=0, column=1, columnspan=2, pady=6, sticky='ew', padx=(0, 3))
        
        path_entry_widget = create_path_entry(
            root=self.root, 
            control_frame=control_frame, 
            path_var=self.entry_path, 
            path_name_str="Input Path"
        )
        path_entry_widget.grid(row=1, column=0, columnspan=3, padx=0, pady=(2, 4), sticky='ew')

        actual_height, grid_bottom = check_frame_geometry(control_frame,"control_frame")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            f"{APP_NAME} Version {__version__}",
        )

    def _run_main(self):
        """
        The core functionality of the app.
        """
        path_str = self._assess_entry_path_str()
        messagebox.showinfo(
            "Main",
            f"Placeholder process on path: {path_str}",
        )
        # ADD REAL FUNCTIONALITY
        
    def _show_app_dir_in_system_explorer(self) -> None:
        """
        Opens the system file explorer to the directory containing
        the exported files, with GUI error handling.
        """
        try:
            target_dir = APP_DIR # Path.home() # et_target_copy_dir()
            pyhabitat.show_system_explorer(path = target_dir)
        except Exception as e:
            # The GUI catches the error to show a user-friendly popup
            messagebox.showerror("Error", f"Could not open system explorer: {e}")

    def _assess_entry_path_str(self):
        entry_path_str = self.entry_path.get().strip()
        if not entry_path_str:
            if not entry_path_str:
                self._display_error("Path not found in current directory.")
                return None

        p = Path(entry_path_str).expanduser().resolve()
        if not p.exists():
            self._display_error(f"File not found at: {p}")
            return None

        return str(p)

    def _display_error(self, message):
        messagebox.showinfo(
            message,
        )
        
def apply_windows_taskbar_icon() -> None:
    """Set a stable Windows AppUserModelID."""

    if not pyhabitat.on_windows():
        return

    try:
        app_id = (
            f"CityOfMemphisWastewater."
            f"{APP_NAME}.Application"
        )

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_id
        )
    except Exception:
        logger.debug(
            "Unable to set Windows taskbar identity",
            exc_info=True,
        )


def start_gui(time_auto_close: int = 0):
    apply_windows_taskbar_icon()

    # 1. Initialize Root and Splash instantly
    root = tk.Tk()
    root.withdraw() # Hide the ugly default window for a split second

    from .splash import SplashFrame
    splash = SplashFrame(root)
    root.update() # Force drawing the splash screen

    # App Initialization
    logger.debug(f"Run {APP_NAME}")
    try:
        app = GuiApp(root=root)
    except Exception as e:
        print(f"Critical Startup Error: {e}",file=sys.stderr)
        logging.debug(f"Startup Error: {e}")
        root.destroy()
        return

    # === Artificial Loading Delay ===4
    DEV_DELAY = False
    if DEV_DELAY:
        import time
        for _ in range(40):
            if not root.winfo_exists(): return
            time.sleep(0.05)
            root.update()
    # ====================================

    # Handover
    if root.winfo_exists():
        splash.teardown() # The Splash cleans itself up

        # Restore window borders/decorations
        root.overrideredirect(False)

        # Re-center the app window before showing it
        # Center and then reveal
        # 2. CONFIG: Set title and geometry while hidden
        if center_window_on_primary is not None:
            center_window_on_primary(root, APP_W, APP_H)

        root.config(cursor="arrow")

        root.deiconify()

        # Focus is safer than 'topmost' for the mouse cursor
        root.focus_force()

        # Only use lift(), avoid wm_attributes("-topmost", True) if possible on WSL
        if not pyhabitat.on_wsl():
            root.lift()
            root.wm_attributes("-topmost", True)
            root.after(200, lambda: root.wm_attributes("-topmost", False))
        else:
            # On WSL, just lift and hope for the best without locking the Z-order
            root.lift()

        if pyhabitat.on_windows():
            try:
                hwnd = root.winfo_id()
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except:
                pass

        if time_auto_close > 0:
            root.after(time_auto_close, root.destroy)


        root.mainloop()
    logger.debug(f"{APP_NAME}: gui closed.")


if __name__ == "__main__":
    start_gui()
