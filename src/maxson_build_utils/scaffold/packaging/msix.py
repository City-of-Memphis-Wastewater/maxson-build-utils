# src/maxson_build_utils/scaffold/packaging/msix.py
from __future__ import annotations

from pathlib import Path
import re
from string import Template

from ...helpers import WriteResult, write_str_to_file
from ...names import to_title_case
from ...pyproject import MaxsonPyProject

MSIX_MANIFEST_TEMPLATE = Template(
    """\
<?xml version="1.0" encoding="utf-8"?>
<Package
    xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
    xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
    xmlns:uap5="http://schemas.microsoft.com/appx/manifest/uap/windows10/5"
    xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
    IgnorableNamespaces="uap uap5 rescap">

  <Identity
      Name="$identity_name"
      Publisher="$publisher"
      Version="$version"
      ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>$display_name</DisplayName>
    <PublisherDisplayName>$publisher_display_name</PublisherDisplayName>
    <Description>$description</Description>
    <Logo>Assets\\StoreLogo-50x50.png</Logo>
  </Properties>

  <Resources>
    <Resource Language="en-us" />
  </Resources>

  <Dependencies>
    <TargetDeviceFamily
        Name="Windows.Desktop"
        MinVersion="10.0.17763.0"
        MaxVersionTested="10.0.22000.1" />
  </Dependencies>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

  <Applications>
    <Application
        Id="$app_id"
        Executable="$executable_name"
        EntryPoint="Windows.FullTrustApplication">

      <uap:VisualElements
          DisplayName="$display_name"
          Description="$description"
          BackgroundColor="transparent"
          Square150x150Logo="Assets\\Logo-150x150.png"
          Square44x44Logo="Assets\\SmallLogo-44x44.png">

        <uap:DefaultTile
            Wide310x150Logo="Assets\\WideLogo-310x150.png" />

        <uap:SplashScreen
            Image="Assets\\SplashScreen-620x300.png" />

      </uap:VisualElements>
      <Extensions>
        <uap5:Extension Category="windows.appExecutionAlias">
          <uap5:AppExecutionAlias>
            <uap5:ExecutionAlias Alias="$executable_name" />
          </uap5:AppExecutionAlias>
        </uap5:Extension>
      </Extensions>
    </Application>
  </Applications>
</Package>
"""
)


def format_msix_version(raw_version: str) -> str:
    """Format a semver/pep440 string into a 4-part MSIX quad version (Major.Minor.Build.Revision)."""
    clean_ver = re.sub(r"[^0-9.]", "", raw_version.split("-")[0])
    parts = [p for p in clean_ver.split(".") if p.isdigit()]
    while len(parts) < 4:
        parts.append("0")
    return ".".join(parts[:4])


def render_appx_manifest(
    identity_name: str,
    publisher: str,
    version: str,
    display_name: str,
    description: str,
    app_id: str,
    executable_name: str,
    publisher_display_name: str,
) -> str:
    """Render the AppxManifest XML template."""
    return MSIX_MANIFEST_TEMPLATE.substitute(
        identity_name=identity_name,
        publisher=publisher,
        version=version,
        display_name=display_name,
        description=description,
        app_id=app_id,
        executable_name=executable_name,
        publisher_display_name=publisher_display_name,
    )


def run_init_msix(
    root_dir: Path | str | None = None,
    *,
    publisher: str | None = None,
    publisher_display_name: str | None = None,
    overwrite: bool = False,
) -> list[WriteResult]:
    """Scaffold `msix/AppxManifest.xml` and `msix/AppxManifest_unversioned.xml` targets."""
    pyproject = MaxsonPyProject(root_dir)
    root = Path(root_dir) if root_dir else pyproject.root_dir or Path.cwd()

    msix_dir = root / "packaging" / "msix"
    assets_dir = msix_dir / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Read config from [tool.maxson-build-utils.packaging.msix] or [tool.maxson-build-utils.msix]
    msix_cfg = (
        pyproject.get("tool", "maxson-build-utils", "packaging", "msix")
        or pyproject.get("tool", "maxson-build-utils", "msix")
        or {}
    )

    app_name = pyproject.import_name or "app"
    display_name = pyproject.pretty_name or to_title_case(app_name)
    description = (
        pyproject.get("project", "description")
        or f"A desktop application for {display_name}."
    )

    # Resolve publisher metadata hierarchy: explicit arg -> pyproject.toml -> generic fallback
    resolved_publisher = (
        publisher
        or msix_cfg.get("publisher")
        or "CN=Development"
    )
    resolved_publisher_display_name = (
        publisher_display_name
        or msix_cfg.get("publisher_display_name")
        or "Developer"
    )

    msix_version = format_msix_version(pyproject.version)
    identity_name = (
        msix_cfg.get("identity_name")
        or f"{resolved_publisher_display_name.replace(' ', '')}.{to_title_case(app_name).replace(' ', '')}"
    )
    executable_name = f"{app_name}.exe"

    results: list[WriteResult] = []

    # 1. Unversioned Template (AppxManifest_unversioned.xml)
    unversioned_text = render_appx_manifest(
        identity_name=identity_name,
        publisher=resolved_publisher,
        version="@@VERSION_PLACEHOLDER@@",
        display_name=display_name,
        description=description,
        app_id=app_name,
        executable_name=executable_name,
        publisher_display_name=resolved_publisher_display_name,
    )
    results.append(
        write_str_to_file(
            msix_dir / "AppxManifest_unversioned.xml",
            text=unversioned_text,
            overwrite=overwrite,
        )
    )

    # 2. Rendered Versioned Manifest (AppxManifest.xml)
    versioned_text = render_appx_manifest(
        identity_name=identity_name,
        publisher=resolved_publisher,
        version=msix_version,
        display_name=display_name,
        description=description,
        app_id=app_name,
        executable_name=executable_name,
        publisher_display_name=resolved_publisher_display_name,
    )
    results.append(
        write_str_to_file(
            msix_dir / "AppxManifest.xml",
            text=versioned_text,
            overwrite=overwrite,
        )
    )

    return results