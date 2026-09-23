# src/maxson_build_utils/vendor.py
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Generator

PROJECT_ROOT = Path(__file__).resolve().parent.parent 

VENDOR_SITE_PACKAGES_DIR = PROJECT_ROOT / "vendor" / "site-packages"
VENDOR_WHEELS_DIR = PROJECT_ROOT / "vendor" /" wheels"
DIST_WHEELS_DIR = PROJECT_ROOT / "dist" / "whl"

DEFAULT_EXTRA_ARGS = ["--no-binary", ":all:"]

@contextmanager
def export_runtime_requirements() -> Generator[Path, None, None]:
    """Generates a temporary requirements.txt from pyproject.toml and guarantees cleanup."""
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix="-requirements.tmp", delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        subprocess.run(
            [
                "uv",
                "export",
                "--format",
                "requirements-txt",
                "--no-editable",
                "--no-dev",
                "--no-emit-project",
                "-o",
                str(tmp_path),
            ],
            check=True,
        )
        yield tmp_path
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def run_vendor_wheels(
    dist_dir: Path | str = DIST_WHEELS_DIR,
    vendor_dir: Path = VENDOR_WHEELS_DIR,
) -> None:
    """Builds project wheel and downloads all runtime dependencies offline, in this case for Flatpak."""
    dist_dir = Path(dist_dir)
    vendor_dir = Path(vendor_dir)

    vendor_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build the project wheel
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(dist_dir)], check=True)

    # 2. Export third-party dependencies & download wheels
    with export_runtime_requirements() as req_file:
        cmd = [
            "uv",
            "run",
            "pip",
            "download",
            "-r",
            str(req_file),
            "-d",
            str(vendor_dir),
        ]

        subprocess.run(cmd, check=True)

    # 3. Stage the built primary wheel into vendor_dir
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No built wheels found in {dist_dir}")

    latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    shutil.copy(latest_wheel, vendor_dir / latest_wheel.name)


def run_vendor_site_packages(
    vendor_dir: Path = VENDOR_SITE_PACKAGES_DIR,
    extra_args: list[str] | None = DEFAULT_EXTRA_ARGS,
    reinstall: bool = False,
) -> None:
    """Exports third-party runtime dependencies as unpacked site-packages into a target directory, in this case for Buildozer."""
    vendor_dir = Path(vendor_dir)
    vendor_dir.mkdir(parents=True, exist_ok=True)

    with export_runtime_requirements() as req_file:
        cmd = [
            "uv",
            "pip",
            "install",
            "-r",
            str(req_file),
            "--target",
            str(vendor_dir),
        ]
        if reinstall:
            cmd.append("--reinstall")
        if extra_args:
            cmd.extend(extra_args)

        subprocess.run(cmd, check=True)
