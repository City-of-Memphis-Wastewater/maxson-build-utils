# src/maxson_build_utils/scaffold/packaging/pyinstaller.py

from __future__ import annotations

from pathlib import Path
from string import Template
#from typing import Sequence

from ...helpers import write_str_to_file, WriteResult
from ...pyproject import MaxsonPyProject

# .packaging/pyinstaller.py
PYINSTALLER_TEMPLATE = Template(
    '''\
#!/usr/bin/env python3
# packaging/pyinstaller/pyinstaller.py

"""
Builds the standalone binary using maxson_build_utils.
"""

from __future__ import annotations

from $import_name._version import __version__
#from $import_name.paths import get_icns_icon, get_ico_icon # update and improve, unclear
from maxson_build_utils.build.pyinstaller import run_build_executable

if __name__ == "__main__":
    run_build_executable(
        src_folder_name="$import_name", 
        version=__version__,
        #icon_ico_path=get_ico_icon(), # update and improve, unclear
        #icon_icns_path=get_icns_icon(), # update and improve, unclear
        collect_data_pkgs=["$import_name"], 
        collect_binary_pkgs=[],
    )
    ''')

def render_pyinstaller_stub_py(import_name: str) -> str:
    """Render the standard forwarded pyinstaller.py content."""
    return PYINSTALLER_TEMPLATE.substitute(import_name=import_name)


def run_init_pyinstaller(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Scaffold pyinstaller.py inside packaging/pyinstaller/."""
    pyproject = MaxsonPyProject(root_dir)

    target_path = pyproject.root_dir / "packaging" / "pyinstaller" / "pyinstaller.py"

    text = render_pyinstaller_stub_py(import_name=pyproject.import_name)

    return write_str_to_file(target_path, text=text, overwrite=overwrite)
