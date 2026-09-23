# src/pyhabitat/version_info
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import sys
from pathlib import Path  

from ._version import __version__
from .system_info import SystemInfo

# -- Versioning --
PACKAGE_NAME = "pyhabitat"
# Auto-detected at build time (fallback)
FALLBACK_VERSION = "dev"


def get_python_version():
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    py_version = f"py{py_major}{py_minor}"
    return py_version

def form_dynamic_binary_name(package_name: str, package_version: str, py_version: str, os_tag: str, arch: str) -> str:    
    # Use hyphens for the CLI/EXE/ELF name
    return f"{package_name}-{package_version}-{py_version}-{os_tag}-{arch}"


if __name__ == "__main__":
    package_name = PACKAGE_NAME
    package_version = __version__
    py_version = get_python_version()
    sysinfo = SystemInfo()
    os_tag = sysinfo.get_os_tag()
    architecture = sysinfo.get_arch()
    bin_name = form_dynamic_binary_name(
        package_name, 
        package_version, 
        py_version, 
        os_tag, 
        architecture
    )
    print(f"bin_name = {bin_name}")
