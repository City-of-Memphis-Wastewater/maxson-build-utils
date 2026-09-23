#!/usr/bin/env bash
set -euo pipefail

# uv sync --extra kivy --group dev --extra buildozer


#uv pip install \
#  backports.tarfile \
#  certifi \
#  chardet \
#  charset_normalizer \
#  idna \
#  openpyxl \
#  pendulum \
#  requests \
#  suds-py3 \
#  tzdata \
#  urllib3 \
#  --target ./vendor/packages/


# Run from packaging/kivy directory
cd "$(dirname "$0")/../packaging/buildozer"

uv run buildozer android debug

