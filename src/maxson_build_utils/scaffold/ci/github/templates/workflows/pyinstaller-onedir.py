name: Build Canonical Onedir Payload

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  core-build:
    name: Build PyInstaller Onedir
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Project & mbu
        run: pip install .

      - name: Execute Onedir Compilation
        run: mbu build pyinstaller --mode onedir

      - name: Upload Canonical Payload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: canonical-onedir-payload
          path: dist/onedir/
          retention-days: 2
