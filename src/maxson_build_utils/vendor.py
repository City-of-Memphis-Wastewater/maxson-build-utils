# src/maxson_build_utils/vendor.py
import subprocess
from pathlib import Path
import shutil

VENDOR_WHEELS_DIR = Path("vendor/wheels")
VENDOR_PACKAGES_DIR = Path("./vendor/packagess/")

def run_vendor_wheels(dist_dir: Path | str = Path("dist/whl"), vendor_dir: Path = VENDOR_WHEELS_DIR) -> None:
    """Builds project wheel and downloads all runtime dependencies offline for Flatpak."""
    dist_dir = Path(dist_dir)
    vendor_dir = Path(vendor_dir)

    vendor_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build the project wheel first
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(dist_dir)], check=True)

    # 2. Export ONLY third-party runtime dependencies (exclude dev deps and the local project itself)
    req_file = Path("requirements.txt")
    subprocess.run([
        "uv", "export",
        "--format", "requirements-txt",
        "--no-editable",
        "--no-dev",
        "--no-emit-project",
        "-o", str(req_file)
    ], check=True)

    # 3. Download third-party runtime wheels
    subprocess.run([
        "uv", "run", "pip", "download",
        "-r", str(req_file),
        "-d", str(vendor_dir)
    ], check=True)

    # 4. Stage the built primary wheel into ./vendor/wheels without checking PyPI dependencies
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No built wheels found in {dist_dir}")

    latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)

    shutil.copy(latest_wheel, vendor_dir / latest_wheel.name)
        
    """subprocess.run([
        "uv", "run", "pip", "download",
        str(wheels[0]),
        "--no-deps",
        "-d", str(vendor_dir)
    ], check=True)"""

def run_vendor_packages(vendor_dir: Path = VENDOR_PACKAGES_DIR):
    pass
