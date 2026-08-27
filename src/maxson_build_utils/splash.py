# src/maxson_build_utils/splash.py
import tkinter as tk
from tkinter import ttk
#from .tk_utils import center_window_on_primary

class SplashFrame:

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.withdraw()
        self.top.overrideredirect(True)
        self.top.configure(bg="#2b2b2b")

        # 1. Define dimensions
        width, height = 300, 80
        # Use generalized centering
        #center_window_on_primary(self.top, width, height)

        # UI Components
        tk.Label(self.top, text="PDF LINK CHECK", fg="white", bg="#2b2b2b", 
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))

        self.progress = ttk.Progressbar(self.top, mode='indeterminate', length=250)
        self.progress.pack(pady=10, padx=20)
        self.progress.start(15)

        # Force the OS to acknowledge the window's existence
        self.top.update_idletasks()

        # Center and then reveal
        #center_window_on_primary(self.top, width, height)
        self.top.deiconify()

    def teardown(self):
        """Cleanly shutdown the splash window."""
        self.progress.stop()
        self.top.destroy()
