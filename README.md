# maxson-build-utils

Centralized org tooling for PyInstaller, DMG, AppImage, DEB, PYZ, etc.

A convention-optional build and deployment framework, with an opinionated Maxson project scaffold available as a convenience.

The central secret sauce is argument and variable value routing from disk. Icons, references, descriptions, names, paths, it can all be inferred or drawn. We leverage the .persist file where necessary to achieve this but ideally we draw values from the pyproject.toml file and form other expected standard paths.

In this way, wrapped CLI tools like create-dmg or pyonstaller can instead draw in determinstic argument values instead of requiring explicit flags.

Package scaffolding precedes building in most cases, so that manifest files are available.

If you frequently build and distribute Python applications and find yourself repeating the same configuration steps, this tool can significantly accelerate your development and simplify the long-term maintenance of your projects.

## Spotlight IT

ChatGPT or Gemini can provide good Python core logic.
"Fix my problem, tell me the library, write a single script, give me some functions with some arguments."

But how do you run that solution on other computers? For coworkers? For contractors? 

maxson-build-utils provides you with an opinionated canvas. Drop in your special core, wire up the args in the functions to the CLI and the GUI, run the builds, and then you've got a one way ticket to the Windows store. IT will probably say yes.

Shadow IT? No, Spotlight IT

## Installation

```bash
pipx install "maxson-build-utils[pyinstaller]"
```

## Quick Start

Scaffold and edit a new project

```bash
mkdir my-project
cd my-project
mbu init all
# edit core.py with special logic
# edit cli.py and gui.py to expose core features
# edit pyproject.toml to add new dependecies

# sync the local new venv
uv sync --group dev --extra gui --extra pyinstaller
```

Build local artifacts
```bash
mbu build shiv
mbu build pyinstaller
```

Leverage the batteries-included github runners by pushing to github.
This will give you files that may be submitted to the Windows Store, the Apple store, and Linux distribution.
```
git tag v0.1.0
git push origin v0.1.0
# Runners are designed to build and upload artifacts to the release.
gh release create v0.1.0 --title "my-project v0.1.0"
```

## Helptree

See the `maxson-build-utils` Typer CLI structure.

```
maxson-build-utils helptree
```

<p align="center">
  <img src="https://raw.githubusercontent.com/City-of-Memphis-Wastewater/maxson-build-utils/main/assets/maxson-build-utils_v0.1.42_helptree.svg" width="100%" alt="SVG of the CLI helptree">
</p>
