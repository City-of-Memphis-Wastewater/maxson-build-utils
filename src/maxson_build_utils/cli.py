# src/maxson_build_utils/cli.py
import typer
from pathlib import Path

from maxson_build_utils.deb import build_debian_package
from maxson_build_utils.vendor import vendor_wheels

app = typer.Typer(help="Maxson build and packaging tools.")

@app.command(name="prepare-flatpak")
def prepare_flatpak(
    dist_dir: Path = Path("dist"),
    vendor_dir: Path = Path("vendor-wheels")
):
    """Build project wheel and vendor offline dependencies for Flatpak."""
    vendor_wheels(dist_dir=dist_dir, vendor_dir=vendor_dir)

@app.command(name="build-deb")
def build_deb(
    app_name: str = typer.Option("cellshift", "--app-name", help="Package application name"),
    version: str = typer.Option("0.1.0", "--version", help="Version string"),
    arch: str = typer.Option("amd64", "--arch", help="Target architecture")
):
    """Assemble and build a Debian .deb package."""
    build_debian_package(app_name=app_name, version=version, arch=arch)


#def main():
#    app()
# ---


if __name__ == "__main__":
    app()
