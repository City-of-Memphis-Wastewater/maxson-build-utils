#!/usr/bin/env python3
# packaging/pyinstaller/pyinstaller.py

"""
Builds the standalone binary using maxson_build_utils.
"""

from __future__ import annotations

from maxson_build_utils._version import __version__
#from maxson_build_utils.paths import get_icns_icon, get_ico_icon # update and improve, unclear
from maxson_build_utils.build.pyinstaller import run_build_executable

if __name__ == "__main__":
    run_build_executable(
        src_folder_name="maxson_build_utils", 
        version=__version__,
        #icon_ico_path=get_ico_icon(), # update and improve, unclear
        #icon_icns_path=get_icns_icon(), # update and improve, unclear
        collect_data_pkgs=["maxson_build_utils"], 
        collect_binary_pkgs=[],
    )
    