# src/maxson_build_utils/cli.py
import typer
from pathlib import Path

from maxson_build_utils.deb import build_debian_package
from maxson_build_utils.vendor import vendor_wheels
from maxson_build_utils.linux_app_image import build_linux_appimage

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


@app.command(name="build-appimage")
def build_appimage(
    app_dir: Path = typer.Option(..., "--app-dir", help="Path to PyInstaller bundle directory"),
    exe_name: str = typer.Option(..., "--exe-name", help="Dynamic executable binary name"),
    pretty_name: str = typer.Option(..., "--pretty-name", help="Pretty desktop app display name"),
    icon: Path = typer.Option(Path("assets/icon.png"), "--icon", help="Path to source icon file")
):
    """Package a PyInstaller ONEDIR bundle into a standalone Linux AppImage."""
    build_linux_appimage(
        app_dir_path=app_dir,
        dynamic_exe_name=exe_name,
        app_name_pretty=pretty_name,
        icon_src=icon,
    )

#def main():
#    app()
# ---


if __name__ == "__main__":
    app()
