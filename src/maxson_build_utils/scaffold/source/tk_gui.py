# src/maxson_build_utils/scaffold/source/tk_gui.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject
from ...rendering import get_template_context, render_template

GUI_TEMPLATE= '''
#!/usr/bin/env python3
# src/@@import_name@@/tk_gui.py

from __future__ import annotations

import ctypes
import logging
import sys
import tkinter as tk
from maxson_gui_utils.resources import resource_path
from tkinter import messagebox, ttk
import pyhabitat
try:
    from maxson_gui_utils.tk_utils import center_window_on_primary
except ImportError:
    center_window_on_primary = None
try:
    from maxson_gui_utils.external_web_launch import launch_configured_website
except ImportError:
    launch_configured_website = None

from ._version import __version__
from .context import APP_NAME, IMPORT_NAME, CONFIG_PATH, APP_DIR

logger = logging.getLogger(__name__)

APP_WIDTH = 800
APP_HEIGHT = 600


class GuiApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root

        #self._initialize_theme()
        self._configure_window()
        self._create_menubar()
        self._create_widgets()

    def _initialize_theme(self) -> None:
        """Initialize the application theme."""
        theme_dir = resource_path("themes", "forest")


        self.root.tk.call(
            "source",
            str(theme_dir / "forest-light.tcl"),
        )
        self.root.tk.call(
            "source",
            str(theme_dir / "forest-dark.tcl"),
        )

        style = ttk.Style(self.root)
        style.configure(".", padding=2)
        style.configure("TFrame", padding=2)
        style.configure("TLabelFrame", padding=(4, 2))
        style.configure("TButton", padding=4)
        style.configure("TCheckbutton", padding=2)
        style.configure("TRadiobutton", padding=2)

        style.theme_use("forest-dark")

    def _configure_window(self) -> None:
        self.root.title(f"{APP_NAME} v{__version__}")
        self.root.geometry(
            f"{APP_WIDTH}x{APP_HEIGHT}"
        )
        self.root.minsize(600, 400)

        self._set_icon()

    def _set_icon(self) -> None:
        """Set the application icon when available."""
        try:
            icon_path = files(
                f"{IMPORT_NAME}.data.icons"
            ) / "water-green_256x256.png"

            if icon_path.is_file():
                self.icon_img = tk.PhotoImage(
                    file=str(icon_path)
                )
                self.root.iconphoto(
                    True,
                    self.icon_img,
                )
        except Exception:
            logger.debug(
                "Unable to load application icon",
                exc_info=True,
            )

    def _create_menubar(self) -> None:
        """Create the application menu bar."""

        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        options = tk.Menu(
            menubar,
            tearoff=False,
        )

        menubar.add_cascade(
            label="Options",
            menu=options,
        )

        options.add_command(
            label="About",
            command=self._show_about,
        )

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        tools_menu.add_command(label="Show Application Directory ", command=lambda: self._show_app_dir_in_system_explorer())
        tools_menu.add_command(label="Launch Configured Website ", command=lambda: self._launch_configured_website())
        tools_menu.add_command(label="Launch BlindWindow ", command=lambda: self._launch_blindwindow())
        tools_menu.add_command(label="Serve Webapp", command=lambda: self._serve_webapp())

        options.add_separator()

        options.add_command(
            label="Exit",
            command=self.root.destroy,
        )

    def _create_widgets(self):
        """CREATE GENERIC STARTING WIDGET"""

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
        # ADD REAL FUNCTIONALITY
        path_str = self._assess_entry_path_str()
        messagebox.showinfo(
            "Main",
            f"Placeholder process on path: {path_str}",
        )
        
    def _show_app_dir_in_system_explorer(self) -> None:
        """
        Opens the system file explorer to the directory containing
        the exported files, with GUI error handling.
        """
        try:
            target_dir = APP_DIR
            pyhabitat.show_system_explorer(path = target_dir)
        except Exception as e:
            # The GUI catches the error to show a user-friendly popup
            messagebox.showerror("Error", f"Could not open system explorer: {e}")

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


def start_gui(time_auto_close: int = 0)->None:
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
'''

def run_init_gui(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    pyproject = MaxsonPyProject(root_dir)

    text = render_template(
        template_str=GUI_TEMPLATE,
        context=get_template_context(pyproject),
    )

    return write_str_to_file(
        path=pyproject.src_dir / "gui.py",
        text=text,
        overwrite=overwrite,
    )
