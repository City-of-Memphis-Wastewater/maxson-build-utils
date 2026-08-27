import os
import shutil
import subprocess
from pathlib import Path

def build_debian_package(app_name: str, version: str, arch: str) -> Path:
    """Assembles /opt, DEBIAN/control, launcher scripts, and executes dpkg-deb."""
    pkg_dir = Path("deb/pkg")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    # Render control file
    control_in = Path("deb/control").read_text()
    control_out = control_in.replace("__VERSION__", version).replace("__ARCH__", arch)
    (pkg_dir / "DEBIAN").mkdir(exist_ok=True)
    (pkg_dir / "DEBIAN/control").write_text(control_out)
    
    # Run dpkg-deb
    deb_filename = f"{app_name}_{version}_{arch}.deb"
    output_path = Path(f"deb/{deb_filename}")
    subprocess.run(["fakeroot", "dpkg-deb", "--build", str(pkg_dir), str(output_path)], check=True)
    return output_path
