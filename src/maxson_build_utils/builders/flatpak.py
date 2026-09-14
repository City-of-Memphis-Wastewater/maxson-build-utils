# src/maxson_build_utils/builders/flatpak.py
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
import pyhabitat
from pyhabitat import probe_app_mode_mgu

from ..target import get_pyproject
from ..vendor import run_vendor_wheels  # or internal vendoring function
from .validate import TargetBuild, validate_build_target

logger = logging.getLogger(__name__)

FLATPAK_DIST_DIR = Path("dist/flatpak")

"""
Look here is the honest to god truth: 
The ideal flatpak process involves the github runner in this repo, reusable-flatpak.yml.
Do you actually want local flatpak builds? The tooling installation is heavy.
The recommended Github runner YML uses the ghcr.io/flathub-infra/flatpak-github-actions:freedesktop-24.08 image, not the flatpat-builder CLI tool used in this file.
"""

def find_flatpak_manifest() -> Path:
    """Locate the flatpak manifest file under packaging/flatpak/."""
    packaging_dir = Path("packaging/flatpak")
    if not packaging_dir.exists():
        raise RuntimeError(
            "packaging/flatpak directory not found. "
            "Run 'mbu init packaging flatpak' to scaffold packaging assets."
        )

    manifests = list(packaging_dir.glob("*.yaml")) + list(packaging_dir.glob("*.yml"))
    if not manifests:
        raise RuntimeError("No Flatpak manifest (*.yaml/*.yml) found in packaging/flatpak/.")

    return manifests[0]


def check_cmd(cmd_str:str)->None:
    if shutil.which(cmd_str) is None:
        raise RuntimeError(
            f"Local Flatpak builds require {cmd_str}. "
            "Please install {cmd_str} locally or,"
            "use the GitHub Flatpak workflow to build the .flatpak bundle."
        )

def build_flatpak(
    manifest_path: Path | None = None,
    output_dir: Path = FLATPAK_DIST_DIR,
) -> Path:
    """Builds a Flatpak single-file bundle using local flatpak-builder toolchain."""

    if pyhabitat.on_termux(): #shutil.which("flatpak-builder") is None:
        raise RuntimeError(
            "Local Flatpak builds require flatpak-builder and flatpak. "
            "These tools are not available in Termux. "
            "Use the GitHub Flatpak workflow to build the .flatpak bundle."
        )

    check_cmd("flatpak-builder")
    check_cmd("flatpak")

    # 1. Enforce AppMode.GUI requirement
    validate_build_target(TargetBuild.FLATPAK)

    run_vendor_wheels(dist_dir=Path("dist/whl"), vendor_dir=Path("build/vendor-wheels"))

    # 2. Check system build tools
    if shutil.which("flatpak-builder") is None:
        raise RuntimeError(
            "flatpak-builder is not installed on this system. "
            "Install it via your package manager (e.g. 'sudo apt install flatpak-builder')."
        )

    if manifest_path is None:
        manifest_path = find_flatpak_manifest()

    if not manifest_path.exists():
        raise FileNotFoundError(f"Flatpak manifest not found at {manifest_path}")

    # 3. Build fresh wheel artifact in dist/ prior to running flatpak-builder
    logger.info("Building wheel artifact for Flatpak packaging...")
    subprocess.run(["uv", "build", "--wheel","--out-dir","dist/whl/"], check=True)

    # 4. Infer metadata matching reusable-flatpak.yml logic
    app_id = manifest_path.stem
    app_name = app_id.rsplit(".", 1)[-1]
    
    project = get_pyproject()
    version = project.version

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_name = f"{app_name}-{version}-x86_64.flatpak"
    bundle_path = output_dir / bundle_name

    build_dir = Path(".flatpak-builder/build")
    repo_dir = Path(".flatpak-builder/repo")

    logger.info(f"Building Flatpak bundle for {app_id}...")

    # Build directory structure
    subprocess.run(
        [
            "flatpak-builder",
            "--force-clean",
            "--repo", str(repo_dir),
            str(build_dir),
            str(manifest_path),
        ],
        check=True,
    )

    branch_name = "main"  # or read from manifest/config

    # Export to .flatpak bundle
    subprocess.run(
        [
            "flatpak",
            "build-bundle",
            str(repo_dir),
            str(bundle_path),
            app_id,
            branch_name,
        ],
        check=True,
    )

    logger.info(f"Successfully generated Flatpak bundle: {bundle_path}")
    return bundle_path
