# src/maxson_build_utils/scaffold/source/gui.py
from __future__ import annotations
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject
from ...rendering import get_template_context, render_template

GUI_TEMPLATE= '''
#!/usr/bin/env python3
# src/@@import_name@@/gui.py

from __future__ import annotations

import ctypes
import logging
import sys
import tkinter as tk
from importlib.resources import files
from tkinter import messagebox, ttk

import pyhabitat

from ._version import __version__
from .context import APP_NAME, IMPORT_NAME

logger = logging.getLogger(__name__)

APP_WIDTH = 800
APP_HEIGHT = 600


class GuiApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root

        self._initialize_theme()
        self._configure_window()
        self._create_menubar()
        self._create_widgets()

    def _initialize_theme(self) -> None:
        """Initialize the application theme."""

        theme_dir = files(
            f"{IMPORT_NAME}.data.themes.forest"
        )

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

        options.add_separator()

        options.add_command(
            label="Exit",
            command=self.root.destroy,
        )

    def _create_widgets(self) -> None:
        """Create application widgets."""

        frame = ttk.Frame(
            self.root,
            padding=12,
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        label = ttk.Label(
            frame,
            text=f"{APP_NAME} v{__version__}",
        )
        label.pack()

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            f"{APP_NAME}\n\nVersion {__version__}",
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


def start_gui() -> None:
    """Start the graphical application."""

    apply_windows_taskbar_icon()

    root = tk.Tk()
    root.withdraw()

    logger.debug("Starting %s", APP_NAME)

    try:
        app = GuiApp(root)
    except Exception:
        logger.exception("GUI startup failed")
        root.destroy()
        return

    root.deiconify()
    root.mainloop()

    logger.debug("%s: GUI closed", APP_NAME)


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
