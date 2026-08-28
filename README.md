# maxson-build-utils

Centralized org tooling for PyInstaller, DMG, AppImage, DEB, PYZ, etc.

A convention-optional build and deployment framework, with an opinionated Maxson project scaffold available as a convenience.

## Spotlight IT

ChatGPT or Gemini can provide good Python core logic.
"Fix my problem, tell me the library, write a single script, give me some functions with some arguments."

But how do you run that solution on other computers? For coworkers? For contractors? 

maxson-build-utils provides you with a blank canvas. Drop in your special core, wire up the args in the functions to the CLI and the GUI, run the builds, and then you've got a one way ticket to the Windows store. IT will probably say yes.

Shadow IT? No, Spotlight IT

## Quick Start

Scaffold and edit a new project

```bash
mkdir my-project
cd my-project
mbu init all
# edit core.py with special logic
# edit cli.py and gui.py to expose core features
# edit pyproject.toml to add new deependecies
```

Build local artifacts
```bash
mbu build shiv
mbu build pyinstaller
```

Leverage the batteries-included github runners by pushing to github.
This will give you assets for the Windows Store, the Apple store, and Linux distribution.
```
git tag v*
git push origin v*
gh release *
```

## Installation

```bash
pipx install "maxson-build-utils[pyinstaller]"
```

## Helptree

See the `maxson-build-utils` Typer CLI structure.

```
maxson-build-utils helptree
```

<p align="center">
  <img src="https://raw.githubusercontent.com/City-of-Memphis-Wastewater/maxson-build-utils/main/assets/maxson-build-utils_v0.1.37_helptree.svg" width="100%" alt="SVG of the CLI helptree">
</p>
