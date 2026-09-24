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

# Prefer mbu target resolution if available; fall back to standalone SPECPATH arithmetic
try:
    from maxson_build_utils.core.know_target import get_target_project_root, get_src_dir
    project_root = get_target_project_root()
    src_dir = get_src_dir()
except ImportError:
    # SPECPATH is provided globally by PyInstaller during spec execution
    project_root = Path(SPECPATH).resolve().parents[1]
    src_dir = project_root / "src"

pathex = [str(src_dir)]

datas = []
binaries = []
hiddenimports = []

# Package Data Collections
datas += collect_data_files('maxson_build_utils')
datas += collect_data_files('maxson_gui_utils')

# Package Binary/DLL Collections
# None

# Hidden Submodule Collections
hiddenimports += collect_submodules('typer')
hiddenimports += collect_submodules('click')
hiddenimports += collect_submodules('rich')
hiddenimports += collect_submodules('maxson_gui_utils')
hiddenimports += collect_submodules('blindwindow')

# Package Metadata Copies
datas += copy_metadata('typer')
datas += copy_metadata('click')
datas += copy_metadata('rich')

# Custom Application Data Directory
app_data_dir = src_dir / "maxson_build_utils" / "data"
if app_data_dir.exists():
    datas.append((str(app_data_dir), "maxson_build_utils/data"))

a = Analysis(
    [str(src_dir / "maxson_build_utils" / "__main__.py")],
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
    name="maxson_build_utils",
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
    name="maxson_build_utils",
)
