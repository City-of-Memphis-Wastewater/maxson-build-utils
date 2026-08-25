# src/maxson_build_utils/scaffold/pyproject.py

from __future__ import annotations

import json
from pathlib import Path
from string import Template

from maxson_build_utils.context import APP_NAME

from ..helpers import write_str_to_file, WriteResult
from ..pyproject import MaxsonPyProject, PyProject
from ..config import get_config_mngr
from ..names import to_pascal_case, get_default_identity_name
config_mngr = get_config_mngr()


# ---------------------------------------------------------------------------
# Maxson project conventions
# ---------------------------------------------------------------------------

REQUIRES_PYTHON = ">=3.10"

DEFAULT_DEPENDENCIES = [
    "dworshak-config>=0.2.8",
    "pyhabitat>=1.3.9",
    "typer>=0.27.0",
    "typer-helptree>=0.2.12",
]

DEFAULT_DEV_DEPENDENCIES = [
    "build>=1.3.0",
    "pyinstaller>=6.17.0 ; platform_system == 'Linux' and platform_machine != 'aarch64'",
    "shiv>=1.0.8",
    "ruff>=0.7.0 ; platform_system == 'Linux' and platform_machine != 'aarch64'",
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

DEFAULT_TEST_DEPENDENCIES = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

DEFAULT_CLASSIFIERS = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
    "Typing :: Typed",
    "Development Status :: 3 - Alpha",
]


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------

PYPROJECT_TEMPLATE = Template(
    """\
[project]
name = $name
dynamic = ["version"]
description = $description
readme = "README.md"
requires-python = $requires_python

dependencies = [
$dependencies
]

license = "MIT"
license-files = ["LICENSE"]

authors = [
    { name = $author_name, email = $author_email }
]

maintainers = [
    { name = $author_name, email = $author_email }
]

classifiers = [
$classifiers
    #"Development Status :: 4 - Beta",
    #"Development Status :: 5 - Production/Stable",
]

keywords = [
$keywords
]

[project.urls]
Homepage = $homepage
Repository = $repository
Issues = $issues
Changelog = $changelog

[project.scripts]
$script_name = $script_target

[dependency-groups]
test = [
$test_dependencies
]
dev = [
    { include-group = "test" },
$dev_dependencies
]


[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

[tool.uv.sources]
$name = { path = $source_path }

[tool.setuptools.dynamic]
version = { file = $version_file }

[tool.setuptools.package-data]
$import_name = [
    "data/*",
    "data/icons/*",
    "data/icons/**/*",
]

[tool.maxson-build-utils.names]
import = $import_name
pretty = $pretty_name

[tool.maxson-build-utils.pyinstaller]
mode = "onedir"
windowed = false
collect_data_pkgs = [$import_name]
collect_binary_pkgs = []

[tool.maxson-build-utils.packaging.msix]
publisher = $windows_publisher_cn
publisher_display_name = $windows_publisher_display_name
identity_name = $windows_publisher_identity_name
"""
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _toml_string(value: str) -> str:
    """Return a safely quoted TOML basic string."""
    return json.dumps(value)


def _toml_array(items: list[str]) -> str:
    """Render strings as an indented TOML array body."""
    return "\n".join(
        f"    {_toml_string(item)},"
        for item in items
    )


def _project_url(
    pyproject: MaxsonPyProject,
    key: str,
    default: str = "",
) -> str:
    """Read a project URL, returning a default when it is absent."""
    value = pyproject.get("project", "urls", key)
    return default if value is None else str(value)


def _keywords(pyproject: MaxsonPyProject) -> list[str]:
    """Return existing project keywords, or a small useful default."""
    value = pyproject.get("project", "keywords")

    if value is None:
        return []

    return [str(item) for item in value]

def _get_git_config(key: str) -> str | None:
    """Read a git config value if available."""
    import subprocess
    try:
        res = subprocess.run(
            ["git", "config", "get", key],
            capture_output=True,
            text=True,
            check=False,
        )
        val = res.stdout.strip()
        return val if val else None
    except Exception:
        return None


def _author_info(pyproject: MaxsonPyProject) -> tuple[str, str]:
    """Determine author name and email dynamically."""
    existing = pyproject.get("project", "authors")
    if isinstance(existing, list) and existing and isinstance(existing[0], dict):
        name = existing[0].get("name")
        email = existing[0].get("email")
        if name and email:
            return str(name), str(email)

    git_name = _get_git_config("user.name")
    git_email = _get_git_config("user.email")

    return (
        git_name or "Your Name",
        git_email or "you@example.com",
    )

def _description(pyproject: MaxsonPyProject) -> str:
    """Return the existing project description, or a useful placeholder."""
    value = pyproject.get("project", "description")

    if value is None:
        return "A Python application."

    return str(value)


def _dependencies(pyproject: MaxsonPyProject) -> list[str]:
    """Return existing dependencies, or the standard Maxson dependencies."""
    value = pyproject.get("project", "dependencies")

    if value is None:
        return list(DEFAULT_DEPENDENCIES)

    return [str(item) for item in value]


def _script_name(pyproject: MaxsonPyProject) -> str:
    """Determine the primary console-script name."""
    scripts = pyproject.get("project", "scripts")

    if isinstance(scripts, dict) and scripts:
        return next(iter(scripts))

    return str(pyproject.app_name)


def _repository_url(pyproject: MaxsonPyProject) -> str:
    """Return the repository URL when already present."""
    return _project_url(pyproject, "Repository")


def _homepage_url(pyproject: MaxsonPyProject) -> str:
    """Return the homepage URL when already present."""
    return _project_url(pyproject, "Homepage")


def _issues_url(pyproject: MaxsonPyProject) -> str:
    """Return the issues URL when already present."""
    return _project_url(pyproject, "Issues")


def _changelog_url(pyproject: MaxsonPyProject) -> str:
    """Return the changelog URL when already present."""
    return _project_url(pyproject, "Changelog")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_pyproject(pyproject: MaxsonPyProject) -> str:
    """Render the canonical Maxson pyproject.toml."""

    import_raw = pyproject.import_name
    author_name, author_email = _author_info(pyproject)

    # 1. Retrieve config values via dworshak-config manager
    raw_publisher_cn = config_mngr.get(service="msix", item="publisher-cn")
    raw_publisher_display_name = config_mngr.get(service="msix", item="publisher-display-name")

    # 2. Resolve publisher defaults
    pub_cn = raw_publisher_cn or "CN=Development"
    pub_display_name = raw_publisher_display_name or author_name or "Developer"

    # Ensure CN prefix formatting if raw GUID or Subject is supplied without 'CN='
    if not pub_cn.startswith("CN="):
        pub_cn = f"CN={pub_cn}"

    # Pass raw values—get_default_identity_name handles parsing and capitalization
    pub_identity = get_default_identity_name(pub_display_name, pyproject.app_name)

    return PYPROJECT_TEMPLATE.substitute(
        name=_toml_string(pyproject.app_name),
        description=_toml_string(_description(pyproject)),
        requires_python=_toml_string(REQUIRES_PYTHON),

        dependencies=_toml_array(
            _dependencies(pyproject)
        ),
        author_name=_toml_string(author_name),
        author_email=_toml_string(author_email),

        classifiers=_toml_array(
            DEFAULT_CLASSIFIERS
        ),

        keywords=_toml_array(
            _keywords(pyproject)
        ),

        homepage=_toml_string(
            _homepage_url(pyproject)
        ),
        repository=_toml_string(
            _repository_url(pyproject)
        ),
        issues=_toml_string(
            _issues_url(pyproject)
        ),
        changelog=_toml_string(
            _changelog_url(pyproject)
        ),

        script_name=_toml_string(
            _script_name(pyproject)
        ),

        script_target=_toml_string(
            f"{pyproject.import_name}.__main__:app"
        ),

        test_dependencies=_toml_array(
                        DEFAULT_TEST_DEPENDENCIES
        ),

        dev_dependencies=_toml_array(
            DEFAULT_DEV_DEPENDENCIES
        ),

        source_path=_toml_string(
            f"src/{pyproject.import_name}"
        ),
        version_file=_toml_string(
            f"src/{pyproject.import_name}/VERSION"
        ),

        import_raw=import_raw,
        import_name=_toml_string(import_raw),

        pretty_name=_toml_string(
            pyproject.pretty_name
        ),

        windows_publisher_cn=_toml_string(pub_cn),
        windows_publisher_display_name=_toml_string(pub_display_name),
        windows_publisher_identity_name=_toml_string(pub_identity),
    )


# ---------------------------------------------------------------------------
# Scaffold entry point
# ---------------------------------------------------------------------------

def run_init_pyproject(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    pyproject = MaxsonPyProject(root_dir)

    text = render_pyproject(pyproject)

    path_pyproject = pyproject.path
    if path_pyproject is None:
        path_pyproject = Path.cwd() / "pyproject.toml"

    path = write_str_to_file(
        path_pyproject,
        text=text,
        overwrite=overwrite,
    )

    pyproject = MaxsonPyProject(root_dir)

    # Check for missing __main__.py and warn user
    main_py = pyproject.src_dir / "__main__.py"
    if not main_py.exists():
        print(
            f"  ⚠️ Warning: Entrypoint '{main_py.relative_to(pyproject.root_dir)}' missing.\n"
            f"     Run `mbu init __main__` to generate it."
        )

    return path
