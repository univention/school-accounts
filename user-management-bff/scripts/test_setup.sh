#!/usr/bin/env sh
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Setup script for automated tests

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UV_SYSTEM_PYTHON=1

cd $PROJECT_DIR

pip install uv=="$UV_VERSION"
uv pip install .

./scripts/translate.sh
