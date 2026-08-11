# Changelog

All notable changes to this project will be documented in this file.
The format is (read: strives to be) based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.7] - 2026-08-10
### Changed:
- Leverage the internal call to consuming-app-based build_executable.py in reusable_appimage.py, for tighter integration, to avoid mutli job race conditon and instead act in series.

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
