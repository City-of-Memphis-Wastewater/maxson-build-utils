import subprocess
from pathlib import Path

def vendor_wheels(dist_dir: Path = Path("dist"), vendor_dir: Path = Path("vendor-wheels")) -> None:
    """Builds project wheels and downloads all transitive dependencies offline, like for Flatpak."""
    vendor_dir.mkdir(parents=True, exist_ok=True)
    
    # Build project wheel first
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(dist_dir)], check=True)
    
    # Download binary wheels for all offline sandbox dependencies
    wheel = list(dist_dir.glob("*.whl"))[0]
    subprocess.run([
        "uv", "pip", "download",
        str(wheel),
        "-d", str(vendor_dir)
    ], check=True)
