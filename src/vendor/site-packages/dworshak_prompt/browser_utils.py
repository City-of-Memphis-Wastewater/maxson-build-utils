# src/dworshak_prompt/browser_utils.py
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import random
import concurrent.futures
import socket
import urllib.request
import urllib.error
import pyhabitat

# Setup Logging
import logging
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Constants & User Messages
# ──────────────────────────────────────────────────────────────────────────────

WSL_VIEW_GUIDE_URL = "https://wslutiliti.es/wslu/install.html"

WSL_HINT_TEMPLATES = [
    (
        "In WSL, auto-opening the browser usually needs one quick setup step.\n"
        "Recommended: install wslu (provides wslview)\n"
        "    sudo apt update && sudo apt install wslu\n"
        "\n"
        "Manual link: {url}\n"
        "More: {guide}"
    ),
    (
        "WSL detected — browser auto-launch may require extra setup.\n"
        "Fastest fix: sudo apt install wslu\n"
        "Then retry. Or open manually:\n"
        "    {url}\n"
        "Guide: {guide}"
    ),
]

def get_wsl_browser_hint(url: str) -> str:
    template = random.choice(WSL_HINT_TEMPLATES)
    return template.format(url=url, guide=WSL_VIEW_GUIDE_URL)


# ──────────────────────────────────────────────────────────────────────────────
# Detection Helpers
# ──────────────────────────────────────────────────────────────────────────────

def is_wsl() -> bool:
    return pyhabitat.on_wsl()


def is_termux() -> bool:
    return pyhabitat.on_termux()


# ──────────────────────────────────────────────────────────────────────────────
# Launch Strategies (each returns True if it thinks it succeeded)
# ──────────────────────────────────────────────────────────────────────────────

def try_termux_browser(url: str) -> bool:
    if not is_termux():
        return False
    if not shutil.which("termux-open-url"):
        return False
    try:
        subprocess.Popen(
            ["termux-open-url", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as e:
        print(f"[WEBPROMPT] termux-open-url failed: {e}", file=sys.stderr)
        return False


def try_wslview(url: str) -> bool:
    if not shutil.which("wslview"):
        return False
    try:
        logger.info("[WEBPROMPT] Launching with wslview...")
        subprocess.Popen(
            ["wslview", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as e:
        logger.warning(f"[WEBPROMPT] wslview failed: {e}", file=sys.stderr)
        return False


def try_windows_powershell(url: str) -> bool:
    ps_path = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
    if not os.path.exists(ps_path):
        return False
    try:
        print("[WEBPROMPT] Launching via PowerShell Start-Process...")
        cmd = f'Start-Process "{url}"'
        subprocess.Popen(
            [ps_path, "-NoProfile", "-Command", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as e:
        print(f"[WEBPROMPT] PowerShell launch failed: {e}", file=sys.stderr)
        return False


def try_windows_cmd(url: str) -> bool:
    cmd_path = "/mnt/c/Windows/System32/cmd.exe"
    if not os.path.exists(cmd_path):
        return False
    try:
        print("[WEBPROMPT] Launching via cmd.exe start...")
        subprocess.Popen(
            [cmd_path, "/c", f'start "" "{url}"'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as e:
        print(f"[WEBPROMPT] cmd.exe launch failed: {e}", file=sys.stderr)
        return False


def try_microsoft_edge_direct(url: str) -> bool:
    edge_bin = shutil.which("microsoft-edge")
    if not edge_bin:
        return False

    env = os.environ.copy()
    env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
    env["PASSWORD_STORE"] = "basic"
    env["CHROME_LOG_LEVEL"] = "3"

    log_path = os.path.expanduser("~/.cache/dworshak_browser.log")
    if os.path.exists(log_path) and os.path.getsize(log_path) > 10 * 1024 * 1024:
        open(log_path, 'w').close()
    env["CHROME_LOG_FILE"] = log_path

    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.Popen(
                [
                    edge_bin,
                    url,
                    "--no-first-run",
                    "--quiet",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--remote-debugging-port=0",
                ],
                stdout=devnull,
                stderr=devnull,
                env=env,
                start_new_session=True,
            )
        return True
    except Exception as e:
        print(f"[WEBPROMPT] Edge direct launch failed: {e}", file=sys.stderr)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def launch_browser(url: str, timeout_sec: float = 2.0) -> bool:
    """Try to open url in a browser. Returns True if launch was attempted."""
    if is_termux():
        return try_termux_browser(url)

    launched = False

    if is_wsl():
        # WSL: prefer reliable Windows bridges, avoid xdg-open
        strategies = [
            try_wslview,
            try_windows_powershell,
            try_windows_cmd,
        ]

        for strategy in strategies:
            if strategy(url):
                launched = True
                break

        # Optional: last resort edge if installed in WSL (rarely works well out of the box, requires wslg anyways)
        if not launched:
            launched = try_microsoft_edge_direct(url)

        if not launched:
            print(get_wsl_browser_hint(url), file=sys.stderr)

        return launched

    # Non-WSL Linux / normal desktop
    if shutil.which("xdg-open"):
        env = os.environ.copy()
        env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
        env["PASSWORD_STORE"] = "basic"
        try:
            print("[WEBPROMPT] Launching with xdg-open...")
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            launched = True
        except Exception as e:
            print(f"[WEBPROMPT] xdg-open failed: {e}", file=sys.stderr)

    if not launched:
        try:
            import webbrowser
            webbrowser.open_new_tab(url)
            launched = True
        except Exception as e:
            print(f"[WEBPROMPT] webbrowser fallback failed: {e}", file=sys.stderr)

    return launched

def find_open_port(start: int = 8082, end: int = 8100) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start

def is_server_running(url: str) -> bool:
    """Check if server is up using stdlib only."""
    try:
        # We use a short timeout because it's localhost
        with urllib.request.urlopen(url, timeout=0.5) as response:
            return response.getcode() < 500
    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
        return False
    except Exception:
        return False

# For testing / standalone
if __name__ == "__main__":
    launch_browser("https://example.com")
