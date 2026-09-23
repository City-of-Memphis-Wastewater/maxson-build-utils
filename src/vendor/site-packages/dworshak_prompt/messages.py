# src/dworshak_prompt/messages.py
from __future__ import annotations
import sys

MSG_CRYPTO_EXTRA = [ 
    "To enable cryptography usage, like with dworshak-secret, install the required extras:",
    "  pip install 'dworshak-prompt[crypto]'",
    "",
    "If 'cryptography' fails to build on your platform, install it via your manager first:",
    "  * Termux:     pkg install python-cryptography",
    "  * iSH/Alpine: apk add py3-cryptography",
    "To access the cryptography like this, your venv must be exposed to system site packages.",
    "Like this: uv venv --system-site-packages." 
]

MSG_TYPER_EXTRA = [
    "To enable the full Typer interface, install the required extras:",
    "  pip install 'dworshak-prompt[typer]'"
]

MSG_FULL_EXTRA = [
    "To enable all features, install all extras:",
    "  pip install 'dworshak-prompt[full]'",
]

def stdlib_notify_missing_command_redirect(command: str):
    """
    Detailed notification missing Typer-specific commands with platform-specific guidance.
    """
    msg_missing_command = [
        f"dworshak-prompt [lite]: The '{command}' command is only available in the full CLI. Check installed extras.",
        ""
        ] + MSG_TYPER_EXTRA
    return msg_missing_command

def notify_missing_function_redirect(_function: str):
    """
    Detailed notification missing functions, generically.
    """
    msg_missing_function = [
        f"dworshak-prompt: The '{_function}' function is not available. Check installed extras.",
        "",
        ]
    return msg_missing_function
