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

@app.command(name="vendor-wheels")
def vendor_wheels(
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
    app_pretty_name: str = typer.Option(..., "--pretty-name", help="Pretty desktop app display name"),
    icon: Path = typer.Option(..., "--icon", help="Path to source icon file, PNG preferred"),
    pyinstaller_onedir_exe_path: Path | None= typer.Option(None, "--exe-path", help="PyInstaller generated app filepath. Defaults to internal state.")        
):
    """Package a PyInstaller ONEDIR bundle into a standalone Linux AppImage. This must be run after the build_executable.py script for the application."""
    build_linux_appimage(
        app_name_pretty=app_pretty_name,
        icon_src=icon,
        app_filepath = pyinstaller_onedir_exe_path
    )


if __name__ == "__main__":
    app()
