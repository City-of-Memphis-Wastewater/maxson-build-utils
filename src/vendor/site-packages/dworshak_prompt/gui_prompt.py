# src/dworshak_prompt/gui_prompt.py
from __future__ import annotations
# tkinter workaround for wsl2, first, before other imports
import logging
logger=logging.getLogger(__name__)
from .gui_helpers import init_x11_threads

logger.debug(f"gui_prompt.py, imports..")

init_x11_threads()
try:
    import tkinter as tk
except ImportError:
    tk=None
from typing import Optional
import platform

import pyhabitat

class CustomPromptDialog:
    def __init__(self, root, title, message, suggestion="", hide_input=False):
        self.result = None
        self.hide_input = hide_input
        
        self.root = root
        logger.debug("Set title")
        self.root.title(title)
        logger.debug("Set resizable")
        self.root.resizable(False, False)
        logger.debug("Lift")
        self.root.lift()
        # Set a minimum width and padding
        # We target ~400px width to ensure the title isn't truncated
        logger.debug("Set width")
        min_w, min_h = 400, 150
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        # Center with the new dimensions
        x = (screen_w // 2) - (min_w // 2)
        y = (screen_h // 2) - (min_h // 2)
        self.root.geometry(f"{min_w}x{min_h}+{x}+{y}")
        self.root.minsize(min_w, min_h)

        logger.debug("Label, message")
        tk.Label(self.root, text=message, wraplength=300, justify="left", padx=10, pady=10).pack(fill ="x")

        # Input container
        logger.debug("Build entry frame")
        entry_frame = tk.Frame(self.root, padx=10)
        entry_frame.pack(fill="x")

        self.entry = tk.Entry(entry_frame, font=("sans-serif", 10))
        if hide_input:
            self.entry.config(show="*")
        self.entry.insert(0, suggestion or "")
        self.entry.pack(side="left", expand=True, fill="x")
        self.entry.bind("<Return>", lambda e: self.on_ok())
        self.entry.focus_set()

        # Toggle Button (Only if hide_input is True)
        if hide_input:
            self.toggle_btn = tk.Button(entry_frame, text="Show", command=self.toggle_visibility, width=5)
            self.toggle_btn.pack(side="right", padx=(5, 0))

        # Action Buttons
        logger.debug("Build buttons")
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="OK", command=self.on_ok, width=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Submit Empty String", command=self.on_submit_empty_string, width=16).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.on_cancel, width=5).pack(side="left", padx=5)
        
        logger.debug("Set protocol")
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)
        #self.root.grab_set()  # Make it modal
        #parent.wait_window(self.root)
        logger.debug("Update idletasks")
        self.root.update_idletasks()
        logger.debug("Lift")
        self.root.lift()

        if not pyhabitat.on_wsl():
            logger.debug("Set to topmost")
            if True:
            #try:
                self.root.attributes("-topmost",True)
                self.root.after(
                    200,
                    lambda: self.root.attributes("-topmost",False),
                )
            #except Exception as e:
            #    pass
        logger.debug("Force Focus")
        self.entry.focus_force()

    def toggle_visibility(self):
        if self.entry.cget("show") == "*":
            self.entry.config(show="")
            self.toggle_btn.config(text="Hide")
        else:
            self.entry.config(show="*")
            self.toggle_btn.config(text="Show")

    def on_ok(self):
        self.result = self.entry.get()
        self.root.destroy()

    def on_submit_empty_string(self):
        self.result = ""
        self.root.destroy()

    def on_cancel(self):
        self.root.destroy()

def gui_get_input(message: str, suggestion: str | None = None, hide_input: bool = False) -> Optional[str]:
    logger.debug("gui_get_input invoked.")
    
    # Force thread-safe initialization immediately before any tkinter touch
    #init_x11_threads()
    
    logger.debug("Initializing tk.Tk()")
    try:
        root = tk.Tk()
        root.withdraw()
        logger.debug("tk.Tk() initialized and withdrawn.")
    except Exception as e:
        logger.critical(f"Failed to create root window: {e}")
        return None

    logger.debug("Building CustomPromptDialog")
    dialog = CustomPromptDialog(
        root=root, 
        title="dworshak-prompt", 
        message=message, 
        suggestion=suggestion or "", 
        hide_input=hide_input
    )
    root.deiconify()
    logger.debug("Entering mainloop.")
    root.mainloop()
    return dialog.result
    
