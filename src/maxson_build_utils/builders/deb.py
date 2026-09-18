import os
import shutil
import subprocess
from pathlib import Path
from ..core.know_target import (
    #DEB_DIST_DIR,
    #DEB_PACKAGING_DIR,
    
    get_pyproject
)
def build_debian_package(app_name: str, version: str, arch: str) -> Path:
    """Assembles /opt, DEBIAN/control, launcher scripts, and executes dpkg-deb."""

    if app_name is None or version is None:
        project = get_pyproject()
        app_pretty_name = app_name or project.name
        version = version or project.version

    if arch is None:
        arch = "plchldr"

    pkg_dir = Path("packaging/deb/pkg")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    debian_dir = pkg_dir / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)
    debian_dir.chmod(0o755)
    # Render control file
    control_in = Path("packaging/deb/control").read_text()
    control_out = control_in.replace("__VERSION__", version).replace("__ARCH__", arch)
    (debian_dir / "control").write_text(control_out)

    # Run dpkg-deb
    deb_filename = f"{app_name}_{version}_{arch}.deb"
    output_path = Path(f"dist/deb/{deb_filename}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["fakeroot", "dpkg-deb", "--build", str(pkg_dir), str(output_path)], check=True)
    return output_path
