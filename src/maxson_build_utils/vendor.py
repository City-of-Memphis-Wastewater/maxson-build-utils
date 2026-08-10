# src/maxson_build_utils/vendor.py
import subprocess
from pathlib import Path

def vendor_wheels(dist_dir: Path = Path("dist"), vendor_dir: Path = Path("vendor-wheels")) -> None:
    """Builds project wheel and downloads all runtime dependencies offline for Flatpak."""
    vendor_dir.mkdir(parents=True, exist_ok=True)

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

    # 4. Stage the built primary wheel into vendor-wheels without checking PyPI dependencies
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No built wheels found in {dist_dir}")
        
    subprocess.run([
        "uv", "run", "pip", "download",
        str(wheels[0]),
        "--no-deps",
        "-d", str(vendor_dir)
    ], check=True)