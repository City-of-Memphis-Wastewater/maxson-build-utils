# src/maxson_build_utils/scaffold/pyproject.py

from __future__ import annotations

import json
from pathlib import Path
from string import Template

from ..helpers import write_str_to_file
from ..pyproject import MaxsonPyProject, PyProject
#from ..config import get_config_mngr

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
$script_name = "$import_name.__main__:app"

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
    "data/icons/*",
    "data/icons/**/*",
]

[tool.maxson-build-utils.names]
import = $import_name
pretty = $pretty_name

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
    pyproject: PyProject,
    key: str,
    default: str = "",
) -> str:
    """Read a project URL, returning a default when it is absent."""
    value = pyproject.get("project", "urls", key)
    return default if value is None else str(value)


def _keywords(pyproject: PyProject) -> list[str]:
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


def _author_info(pyproject: PyProject) -> tuple[str, str]:
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

def _description(pyproject: PyProject) -> str:
    """Return the existing project description, or a useful placeholder."""
    value = pyproject.get("project", "description")

    if value is None:
        return "A Python application."

    return str(value)


def _dependencies(pyproject: PyProject) -> list[str]:
    """Return existing dependencies, or the standard Maxson dependencies."""
    value = pyproject.get("project", "dependencies")

    if value is None:
        return list(DEFAULT_DEPENDENCIES)

    return [str(item) for item in value]


def _script_name(pyproject: PyProject) -> str:
    """Determine the primary console-script name."""
    scripts = pyproject.get("project", "scripts")

    if isinstance(scripts, dict) and scripts:
        return next(iter(scripts))

    return str(pyproject.app_name)


def _repository_url(pyproject: PyProject) -> str:
    """Return the repository URL when already present."""
    return _project_url(pyproject, "Repository")


def _homepage_url(pyproject: PyProject) -> str:
    """Return the homepage URL when already present."""
    return _project_url(pyproject, "Homepage")


def _issues_url(pyproject: PyProject) -> str:
    """Return the issues URL when already present."""
    return _project_url(pyproject, "Issues")


def _changelog_url(pyproject: PyProject) -> str:
    """Return the changelog URL when already present."""
    return _project_url(pyproject, "Changelog")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_pyproject(pyproject: PyProject) -> str:
    """Render the canonical Maxson pyproject.toml."""

    import_raw = pyproject.import_name
    author_name, author_email = _author_info(pyproject)

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
        
        #import_name=_toml_string(
        #    pyproject.import_name
        #),
        pretty_name=_toml_string(
            pyproject.pretty_name
        ),
    )


# ---------------------------------------------------------------------------
# Scaffold entry point
# ---------------------------------------------------------------------------

def run_init_pyproject(
    root_dir: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    pyproject = MaxsonPyProject(root_dir)

    text = render_pyproject(pyproject)

    path = write_str_to_file(
        pyproject.path,
        text=text,
        overwrite=overwrite,
    )

    # Check for missing __main__.py and warn user
    main_py = pyproject.src_dir / "__main__.py"
    if not main_py.exists():
        print(
            f"  ⚠️ Warning: Entrypoint '{main_py.relative_to(pyproject.root)}' missing.\n"
            f"     Run `mbu init __main__` to generate it."
        )

    return path
