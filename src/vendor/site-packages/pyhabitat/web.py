"""
pyhabitat.web

Reusable helpers for launching local web applications.

Typical usage
-------------

    from http.server import ThreadingHTTPServer
    from pyhabitat.web import (
        find_open_port,
        launch_browser_after_http_poll,
    )

    port = find_open_port(8000)

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as httpd:

        url = f"http://127.0.0.1:{port}/"

        launch_browser_after_http_poll(url)

        httpd.serve_forever()

The browser is only opened after the server is actually responding,
avoiding arbitrary sleep() delays and startup race conditions.
"""

from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.request
import webbrowser
import urllib.error
from urllib.parse import urlparse, quote
import sys
from pathlib import Path
from typing import Optional

from .environment import on_wsl, on_termux, on_linux, is_android_kivy

logger = logging.getLogger(__name__)

__all__ = [
    'launch_browser_after_http_poll',
    'launch_browser_now',
    'find_open_port',
    'browse_directory',
    'serve_file',
    'serve_directory',
    'shutdown_server',
    'wait_for_server_shutdown',
]

# ----------------------------------------------------------------------
# Port utilities
# ----------------------------------------------------------------------
def find_open_port(
    start_port: int = 0,
    host: str = "127.0.0.1",
    max_attempts: int = 100
) -> int:
    """
    Return an available TCP port, searching upward defensively if contested.

    If start_port==0, let the operating system choose an ephemeral port.
    Otherwise search upward from start.
    """

    if start_port == 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, 0))
            return sock.getsockname()[1]

    #while True:
    for attempt in range(max_attempts):
        port = start_port + attempt
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find an open port starting from {start_port} within {max_attempts} tries.")


# ----------------------------------------------------------------------
# HTTP readiness
# ----------------------------------------------------------------------

def wait_until_http_ready(
    url: str,
    *,
    timeout: float = 5.0,
    poll_interval: float = 0.1,
) -> bool:
    """
    Wait until an HTTP endpoint responds.

    Returns
    -------
    bool
        True if the endpoint became responsive before timeout.
    """

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        try:
            with urllib.request.urlopen(url, timeout=1):
                return True

        except urllib.error.HTTPError:
            # Server answered.
            return True


        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ):
            time.sleep(poll_interval)

    return False


# -----------------
# Browser launching
# -----------------

def _prepare_url(url: str) -> str:
    """
    Normalize user input into a browser-launchable URL.

    Examples
    --------
    google.com              -> https://google.com
    google.com/search       -> https://google.com/search
    localhost:8000          -> http://localhost:8000
    127.0.0.1:5000          -> http://127.0.0.1:5000
    https://example.com     -> unchanged
    file:///tmp/test.html   -> unchanged
    README.html             -> file:///.../README.html
    """

    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    parsed = urlparse(url)

    # Already a fully-qualified URL.
    if parsed.scheme:
        return url

    host = url.split("/", 1)[0]

    # Local development hosts.
    if host.startswith(("localhost", "127.", "0.0.0.0", "[::1]")):
        return f"http://{url}"

    # host:port
    if host.count(":") == 1 and host.rsplit(":", 1)[1].isdigit():
        return f"http://{url}"

    # Bare domain names.
    if "." in host:
        return f"https://{url}"

    # Existing local file.
    path = Path(url).expanduser()
    if path.exists():
        return path.resolve().as_uri()

    # Last resort: assume HTTPS.
    return f"https://{url}"

def launch_browser_now(url: str) -> bool:
    """
    Open a URL using the best available launcher.

    Use case: Launching a local file or external website.

    Alternative: If starting a web app, use launch_browser_after_http_poll().

    Hypothetical alias names:
    - open_static_or_external_url(url)
    - launch_browser_now(url)
    
    Returns
    -------
    bool
        True if a launch command was successfully started.
    """
    url = _prepare_url(url)

    # --- Native Android Kivy ---
    if is_android_kivy():
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            PythonActivity.mActivity.startActivity(intent)
            return True
        except Exception:
            logger.exception("Android JNI intent launch failed")
            return False

    # --- Termux ---
    termux_launcher = shutil.which("termux-open-url")
    if on_termux() and termux_launcher:

        try:
            subprocess.Popen(
                ["termux-open-url", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return True

        except Exception:
            logger.exception("termux-open-url failed")

    # --- WSL / Windows Edge ---
    edge = shutil.which("microsoft-edge")
    if on_wsl() and edge: #edge:
        env = os.environ.copy()
        env["CHROME_LOG_LEVEL"] = "3"
        try:
            subprocess.Popen(
                [
                    edge,
                    url,
                    "--no-first-run",
                    "--quiet",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-sync",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
            )
            return True

        except Exception:
            logger.exception("microsoft-edge failed")

    # --- Linux desktop ---
    linux_launcher = shutil.which("xdg-open")
    if on_linux() and linux_launcher:

        try:
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return True

        except Exception:
            logger.exception("xdg-open failed")

    # --- Generic Python fallback ---
    try:
        webbrowser.open_new_tab(url)
        return True

    except Exception:
        logger.exception("webbrowser failed")
        return False

# ----------------------------------------------------------------------
# Combined helper
# ----------------------------------------------------------------------

def launch_browser_after_http_poll(
    url: str,
    *,
    timeout: float = 5.0,
    poll_interval: float = 0.1,
) -> threading.Thread:
    """
    Launch a daemon thread which waits for an HTTP server to become
    responsive before opening the user's browser.

    Use case: Spinning up a local web app with consideration for thread management and polling.

    Hypothetical alias names:
    - open_local_server_url(url)
    - launch_browser_after_http_poll(url)
    - launch_browser_when_ready(url)
    
    This function returns immediately.

    Parameters
    ----------
    url
        URL to poll and eventually open.

    timeout
        Maximum time to wait.

    poll_interval
        Delay between connection attempts.

    Returns
    -------
    threading.Thread
        The daemon thread performing the wait.
    """

    def worker():

        if wait_until_http_ready(
            url,
            timeout=timeout,
            poll_interval=poll_interval,
        ):

            logger.debug("Server ready: %s", url)

            launch_browser_now(url)

        else:

            logger.warning(
                "Timed out after %.1fs waiting for %s",
                timeout,
                url,
            )

    thread = threading.Thread(
        target=worker,
        daemon=True,
        name=f"launch-browser-when-ready: {url}",
    )

    thread.start()

    return thread

def browse_directory(path, **kwargs):

    url = serve_directory(path, **kwargs)

    launch_browser_now(url)
    print(f"{url}",file=sys.stdout)
    return url



# Cache the active server so repeated calls don't spawn duplicates.
_server: Optional[subprocess.Popen] = None
_server_port: Optional[int] = None
_server_root: Optional[Path] = None
                                                   
def serve_directory(
    path: str | Path,                              
    *,
    host: str = "127.0.0.1",                       
    port: Optional[int] = None,
) -> str:                                          
    """
    Serve a directory using Python's built-in HTTP server.

    Reuses an existing server if it is already serving the requested
    directory.

    Parameters
    ----------
    directory
        Directory to serve.
    host
        Interface to bind.
    port
        Optional fixed port. If omitted, a free port is chosen.

    Returns
    -------
    str
        URL of the directory browser.
    """

    global _server, _server_port, _server_root

    directory = path
    directory = Path(directory).expanduser().resolve()

    if not directory.is_dir():
        raise NotADirectoryError(directory)

    # Reuse an existing server if possible.
    if (
        _server is not None
        and _server.poll() is None
        and _server_root == directory
        and _server_port is not None
    ):
        return f"http://{host}:{_server_port}/"

    # Stop previous server.
    if _server is not None and _server.poll() is None:
        _server.terminate()
        try:
            _server.wait(timeout=2)
        except Exception:
            _server.kill()

    if port is None:
        port = find_open_port(8000, host)
    _server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            host,
            "--directory",
            str(directory),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    _server_root = directory
    _server_port = port

    return f"http://{host}:{port}/"

def serve_file(path:str | Path, *, host="127.0.0.1", port=None):
    path = Path(path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(path)

    root = path.parent

    root_url = serve_directory(root, host=host, port=port)

    #url = root_url + quote(path.name, safe="")
    
    relative = path.relative_to(root)
    url = root_url + quote(relative.as_posix(), safe="/")

    return url

def shutdown_server():
    global _server, _server_port, _server_root

    if _server is not None and _server.poll() is None:
        _server.terminate()
        try:
            _server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _server.kill()

    _server = None
    _server_port = None
    _server_root = None
    

def wait_for_server_shutdown():
    global _server

    if _server is None:
        return

    try:
        _server.wait()

    except KeyboardInterrupt:
        shutdown_server()
