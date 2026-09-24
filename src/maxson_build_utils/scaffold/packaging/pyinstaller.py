# src/maxson_build_utils/scaffold/packaging/pyinstaller.py
from __future__ import annotations

from pathlib import Path

from ...helpers import WriteResult, write_str_to_file
from ...pyproject import MaxsonPyProject
from ...rendering import get_template_context, render_template

PYINSTALLER_SPEC_TEMPLATE = """\
# -*- mode: python ; coding: utf-8 -*-
# Generated automatically by maxson-build-utils

import sys
from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

project_root = Path(__file__).resolve().parents[2]
src_dir = project_root / "src"

pathex = [str(src_dir)]

datas = []
binaries = []
hiddenimports = []

# Package Data Collections
@@data_collections@@

# Package Binary/DLL Collections
@@binary_collections@@

# Hidden Submodule Collections
@@submodule_collections@@

# Package Metadata Copies
@@metadata_collections@@

# Custom Application Data Directory
app_data_dir = src_dir / "@@import_name@@" / "data"
if app_data_dir.exists():
    datas.append((str(app_data_dir), "@@import_name@@/data"))

a = Analysis(
    [str(src_dir / "@@import_name@@" / "__main__.py")],
    pathex=pathex,
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="@@import_name@@",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="@@import_name@@",
)
"""


def run_init_pyinstaller_spec(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> list[WriteResult]:
    """Scaffold packaging/pyinstaller/<import_name>.spec."""
    pyproject = MaxsonPyProject(root_dir)
    root = Path(root_dir) if root_dir else pyproject.root_dir or Path.cwd()

    cfg = pyproject.get("tool", "maxson-build-utils", "pyinstaller") or {}

    data_lines = [f"datas += collect_data_files('{pkg}')" for pkg in cfg.get("collect_data_pkgs", [])]
    bin_lines = [f"binaries += collect_dynamic_libs('{pkg}')" for pkg in cfg.get("collect_binary_pkgs", [])]
    sub_lines = [f"hiddenimports += collect_submodules('{pkg}')" for pkg in cfg.get("collect_submodules_pkgs", [])]
    meta_lines = [f"datas += copy_metadata('{pkg}')" for pkg in cfg.get("collect_metadata_pkgs", [])]

    # Build context and inject custom collection strings
    context = get_template_context(pyproject)
    context.update({
        "data_collections": "\n".join(data_lines) if data_lines else "# None",
        "binary_collections": "\n".join(bin_lines) if bin_lines else "# None",
        "submodule_collections": "\n".join(sub_lines) if sub_lines else "# None",
        "metadata_collections": "\n".join(meta_lines) if meta_lines else "# None",
    })

    spec_dir = root / "packaging" / "pyinstaller"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / f"{pyproject.import_name}.spec"

    text = render_template(
        template_str=PYINSTALLER_SPEC_TEMPLATE,
        context=context,
    )

    result = write_str_to_file(
        path=spec_path,
        text=text,
        overwrite=overwrite,
    )

    return [result]
