# src/pyhabitat/server_runtime.py
from __future__ import annotations
import subprocess
import sys
import json
from pathlib import Path
import os

PID_FILE = Path.home() / ".cache/pyhabitat/servedirs.json"


def write_state(pid: int, port: int, path: str):
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(json.dumps({
        "pid": pid,
        "port": port,
        "path": path
    }))


def read_state():
    if not PID_FILE.exists():
        return None
    return json.loads(PID_FILE.read_text())


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_previous():
    state = read_state()
    if not state:
        return

    pid = state["pid"]

    if is_alive(pid):
        try:
            os.kill(pid, 15)
        except OSError:
            pass

    PID_FILE.unlink(missing_ok=True)
