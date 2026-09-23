# src/pyhabitat/environment.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import platform
import sys
import os
import logging

# On Windows, we need the msvcrt module for non-blocking I/O
try:
    import msvcrt
except ImportError:
    msvcrt = None

logger = logging.getLogger(__name__)

__all__ = [
    'on_termux',
    'on_freebsd',
    'on_linux',
    'on_pydroid',
    'on_chromeos_crostini',
    'on_android',
    'on_windows',
    'on_wsl',
    'on_macos',
    'on_ish_alpine',
    'as_pyinstaller',
    'as_frozen',
    'is_msix',
    'is_android_kivy',
    'in_repl',
    'interp_path',
    'get_interp_shebang'
]

# --- ENVIRONMENT AND OPERATING SYSTEM CHECKS ---
def on_termux() -> bool:
    """Detect if running in Termux environment on Android, based on Termux-specific environmental variables."""
    
    if platform.system() not in ('Linux', 'Android'):
        return False
    
    termux_path_prefix = '/data/data/com.termux'
    
    # Termux-specific environment variable ($PREFIX)
    # The actual prefix is /data/data/com.termux/files/usr
    if os.environ.get('PREFIX', default='').startswith(termux_path_prefix + '/usr'):
        return True
    
    # Termux-specific environment variable ($HOME)
    # The actual home is /data/data/com.termux/files/home
    if os.environ.get('HOME', default='').startswith(termux_path_prefix + '/home'):
        return True

    # Code insight: The os.environ.get command returns the supplied default if the key is not found. 
    #   None is retured if a default is not speficied.
    
    # Termux-specific environment variable ($TERMUX_VERSION)
    if 'TERMUX_VERSION' in os.environ:
        return True
    
    return False

def on_freebsd() -> bool:
    """Detect if running on FreeBSD."""
    return platform.system() == 'FreeBSD'

def on_linux():
    """
    Detect if running on Linux.
    Basic, expected; `platform.system() == 'Linux'` 
    """
    #return platform.system() == 'Linux' 
    return platform.system() in ("Linux", "Android")

def on_android() -> bool:
    """
    Detect if running on Android.
    
    Note: The on_termux() function is more robust and safe for Termux.
    Checking for Termux with on_termux() does not require checking for Android with on_android().

    on_android() will be True on:   
        - Sandboxed IDE's:
            - Pydroid3
            - QPython
        - `proot`-reliant user-space containers:
            - Termux
            - Andronix
            - UserLand
            - AnLinux

    on_android() will be False on:
        - Full Virtual Machines:
            - VirtualBox
            - VMware
            - QEMU      
    """
    
    # Newer Python (3.13+)
    if platform.system() == "Android":
        return True

    # Older Python (Termux / Android still reports Linux)
    if platform.system() == "Linux":
        return "android" in platform.platform().lower()

    return False
    
def on_wsl():
    """Return True if running inside Windows Subsystem for Linux (WSL or WSL2)."""
    # Must look like Linux, not Windows
    if platform.system() != "Linux":
        return False

     
    # --- Check environment variables for WSL2 ---
    # False negative risk: 
    # Environment variables may be absent in older WSL1 installs.
    # False negative likelihood: low.
    if "WSL_DISTRO_NAME" in os.environ or "WSL_INTEROP" in os.environ:
        return True

    # --- Check kernel info for 'microsoft' or 'wsl' string (Fallback) ---
    # False negative risk: 
    # Custom kernels, future Windows versions, or minimal WSL distros may omit 'microsoft' in strings.
    # False negative likelihood: Very low to moderate.
    try:
        with open("/proc/version") as f:
            version_info = f.read().lower() 
            if "microsoft" in version_info or "wsl" in version_info:
                return True
    except (IOError, OSError):
        # This block would catch the PermissionError!
        # It would simply 'pass' and move on.
        pass


    # Check for WSL-specific mounts (fallback)
    """
    /proc/sys/kernel/osrelease
    Purpose: Contains the kernel release string. In WSL, it usually contains "microsoft" (WSL2) or "microsoft-standard" (WSL1).
    Very reliable for detecting WSL1 and WSL2 unless someone compiled a custom kernel and removed the microsoft string.
    
    False negative risk: 
    If /proc/sys/kernel/osrelease cannot be read due to permissions, a containerized WSL distro, or some sandboxed environment.
    # False negative likelihood: Very low.
    """
    try:
        with open("/proc/sys/kernel/osrelease") as f:
            osrelease = f.read().lower()
            if "microsoft" in osrelease:
                return True
    except (IOError, OSError):
    # This block would catch the PermissionError, an FileNotFound
        pass

    try:
        if 'microsoft' in platform.uname().release.lower():
            return True
    except:
        pass    
    return False

def on_pydroid():
    """Return True if running under Pydroid 3 (Android app)."""
    if not on_android():
        return False

    exe = (sys.executable or "").lower()
    if "pydroid" in exe or "ru.iiec.pydroid3" in exe:
        return True

    return any("pydroid" in p.lower() for p in sys.path)

def on_chromeos_crostini() -> bool:
    """
    Detects if running within a Crostini Linux container on ChromeOS.
    Checks for the Sommelier compositor and ChromeOS-specific mount points.
    """
    # 1. Sommelier handles Wayland/X11 bridging from the container to ChromeOS.
    # These variables are injected by the ChromeOS guest environment.
    if "SOMMELIER_VERSION" in os.environ or "SOMMELIER_VM_IDENTIFIER" in os.environ:
        return True

    # 2. ChromeOS maps the host filesystem to /mnt/chromeos.
    # This is a standard architectural feature of Crostini.
    if os.path.exists('/mnt/chromeos'):
        return True

    # 3. Fallback: Check for the 'cros' GTK input module 
    # (present in your environment variables).
    if os.environ.get('GTK_IM_MODULE') == 'cros':
        return True

    return False

def on_windows() -> bool:
    """Detect if running on Windows."""
    return platform.system() == 'Windows'

def on_macos() -> bool:
    """Detect if running on MacOS. Does not consider on_ish_alpine()."""
    return (platform.system() == 'Darwin')

def on_ish_alpine() -> bool:
    """
    Detect if running in iSH Alpine environment on iOS.
    """
    # platform.system() usually returns 'Linux' in iSH

    # iSH runs on iOS but reports 'Linux' via platform.system()
    if platform.system() not in ('Linux', 'iOS','iPadOS'):
        return False
        
    # On iSH, /etc/apk/ will exist. However, this is not unique to iSH as standard Alpine Linux also has this directory.
    # Therefore, we need an additional check to differentiate iSH from standard Alpine.
    # HIGHLY SPECIFIC iSH CHECK: Look for the unique /proc/ish/ directory.
    # This directory is created by the iSH pseudo-kernel and does not exist 
    # on standard Alpine or other Linux distributions.
    if os.path.isdir('/etc/apk/') and os.path.isdir('/proc/ish'):
        # This combination is highly specific to iSH Alpine.
        return True
    
    return False

def in_repl() -> bool:
    """
    Detects if the code is running in the Python interactive REPL (e.g., when 'python' is typed in a console).

    This function specifically checks for the Python REPL by verifying the presence of the interactive
    prompt (`sys.ps1`). It returns False for other interactive terminal scenarios, such as running a
    PyInstaller binary in a console.

    Returns:
        bool: True if running in the Python REPL; False otherwise.
    """
    return hasattr(sys, 'ps1')


def is_msix() -> bool:
    """
    Detect whether the current Python process is running inside an MSIX
    (or APPX) packaged environment, such as when distributed through the
    Microsoft Store.

    This check works by querying the Windows package identity assigned to
    AppX/MSIX containers. If the process has no package identity, Windows
    returns APPMODEL_ERROR_NO_PACKAGE (15700), and the function returns False.

    Returns:
        bool: True if running inside an MSIX/AppX package; False otherwise.

    This function cannot be dual-use for introspection as well as checking arbitrary paths.
    This function is only for introspection  and should accept no arguments.
    """
    if platform.system() != "Windows":
        return False

    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return False

    # Windows API function
    GetCurrentPackageFullName = ctypes.windll.kernel32.GetCurrentPackageFullName
    GetCurrentPackageFullName.argtypes = [
        ctypes.POINTER(wintypes.UINT),
        wintypes.LPWSTR
    ]
    GetCurrentPackageFullName.restype = wintypes.LONG

    APPMODEL_ERROR_NO_PACKAGE = 15700

    length = wintypes.UINT(0)

    # First call: get required buffer length
    rc = GetCurrentPackageFullName(ctypes.byref(length), None)

    if rc == APPMODEL_ERROR_NO_PACKAGE:
        return False  # Not MSIX/AppX packaged

    # Allocate buffer and retrieve the package full name
    buffer = ctypes.create_unicode_buffer(length.value)
    rc = GetCurrentPackageFullName(ctypes.byref(length), buffer)

    return rc == 0

def is_android_kivy() -> bool:
    """Check if running natively inside an Android Kivy app."""
    # Kivy platform detection (or fallback if Kivy isn't installed in the environment)
    try:
        from kivy.utils import platform as KIVY_PLATFORM
    except ImportError:
        KIVY_PLATFORM = None
    if KIVY_PLATFORM == "android":
        return True
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_ENTRYPOINT" in os.environ

# --- BUILD AND EXECUTABLE CHECKS ---
    
def as_pyinstaller():
    """Detects if the Python script is running as a 'frozen' in the course of generating a PyInstaller binary executable."""
    # If the app is frozen AND has the PyInstaller-specific temporary folder path
    return as_frozen() and hasattr(sys, '_MEIPASS')

# The standard way to check for a frozen state:
def as_frozen():
    """
    Detects if the Python script is running as a 'frozen' (standalone) 
    executable created by a tool like PyInstaller, cx_Freeze, or Nuitka.

    This check is crucial for handling file paths, finding resources, 
    and general environment assumptions, as a frozen executable's 
    structure differs significantly from a standard script execution 
    or a virtual environment.

    The check is based on examining the 'frozen' attribute of the sys module.

    Returns:
        bool: True if the application is running as a frozen executable; 
              False otherwise.
    """
    return getattr(sys, 'frozen', False)
    
# --- Interpreter Check ---

def interp_path(debug: bool = False) -> str:
    """
    Returns the path to the Python interpreter binary and optionally prints it.

    This function wraps `sys.executable` to provide the path to the interpreter
    (e.g., '/data/data/com.termux/files/usr/bin/python3' in Termux or the embedded
    interpreter in a frozen executable). If the path is empty (e.g., in some embedded
    or sandboxed environments), an empty string is returned.

    Args:
        print_path: If True, prints the interpreter path to stdout.

    Returns:
        str: The path to the Python interpreter binary, or an empty string if unavailable.
    """
    path = sys.executable
    if debug:
        logging.debug(f"Python interpreter path: {path}")
    return path


def get_interp_shebang() -> str:
    """
    Returns the most compatible shebang for the current platform.
    No hash symbol is included.
    """
    if os.name == 'nt':
        # Generic python call for Windows PATH/Registry association
        return "python" 
    
    # Standard Unix/Termux portable path
    return "/usr/bin/env python3"
