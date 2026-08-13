# Changelog

All notable changes to this project will be documented in this file.
The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.19] - 2026-08-13
### Added:
- Templates for cli, gui, and context, exposed in the init sub app.
- mbu cli alias

---

## [0.1.18] - 2026-08-13
### Added:
- init sub app

---

## [0.1.17] - 2026-08-12
### Added:
- Stock icons carried here in src/*/data/icons/ can be referenced by consumers of this library

---

## [0.1.16] - 2026-08-12
### Changed:
- Return None for missing pyproject.toml values.
- Remove properties from PyProject.toml class
- Allow pyproject CLI command to report missing keys to stderr.
- Exemplify [tool.maxson-build-utils] usage

---

## [0.1.15] - 2026-08-12
### Changed:
- Add version.py and version CLI command
- Remove pyproject.get_toml_value() function in __init__ in favor of pyproject.PyProject

---

## [0.1.14] - 2026-08-12
### Added:
- src/maxson_build_utils/pyproject.py
- CLI command pyproject with stdout printed return

---

## [0.1.13] - 2026-08-11
### Fixed:
- vendor.vendor_wheels() function changed to vendor.run_vendor_wheels()

### Added:
- helptree asset, with README.md reference
- logging_setup.py, with functions for library and app logging

### Changed:
- Leverage typer CLI best practices, included main entry func, debug logging. There is not a gui for this app.

---

## [0.1.12] - 2026-08-11
### Added:
- reusable-flatpak.yml

---

## [0.1.11] - 2026-08-11
### Added:
- LICENSE

---

## [0.1.10] - 2026-08-11
### Changed:
- reusable-appimage.yml is safer now for manual dispatch, when there is no release tag.

---

## [0.1.9] - 2026-08-11
### Changed:
- Store state using config.json with dworshak-config to star vars, rather than to env vars.

---

## [0.1.8] - 2026-08-10
### Fixed:
- reusable-appimage.yml had blatant errors for routing `--exe-path`

---

## [0.1.7] - 2026-08-10
### Changed:
- Leverage the internal call to consuming-app-based build_executable.py in reusable_appimage.py, for tighter integration, to avoid mutli job race conditon and instead act in series.

### Internal:
- Note that it is quintessential that ONEDIR is the default setting for my pyinstaller routing.

---

## [0.1.6] - 2026-08-10
### Fixed:
- Leverage internal state and env vars to capture pyinstaller onedir characteristics for appimage.

---

## [0.1.5] - 2026-08-10
### Fixed:
- Previous approach to running pyinstaller before appimage build, in reusable_appimage.yml, was conflated. We must reference scripts/build_executable.py now, as a standard, or other wise reference the local script that indicates how to build it, feeding the run_build_executable() function.

---

## [0.1.4] - 2026-08-10
### Fixed:
- Don't automatically run appimage build with each pyinstaller run in build_executable.py. Suppress all uses of post_process_linux_build().

---

## [0.1.3] - 2026-08-10
### Fixed:
- .gitignore was uploaded, weird. Adjust build.yml
- try reusable app image runner.

---

## [0.1.2] - 2026-08-10
### Fixed:
- Add tests/test_null.py
- Use context.py, not paths.py, to define and import SRC_FOLDER_NAME

---

## [0.1.1] - 2026-08-10
### Added:
- PyPI release 
- build_pyz, shiv support
- build_executable, pyinstaller and app image support
- deb support
- flatpak support
- CLI and init exposure
- github runners, for publish, ci, and test
- build_pyz.py for CLI

### Fixed:
- Add dev dependency group

---

## [0.1.0] - 2026-08-10
### Added:
- Introduce cellshift use case
- Local development without PyPI release 
