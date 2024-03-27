#!/usr/bin/env sh
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Setup script for automated tests

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd $PROJECT_DIR

pip install poetry=="$POETRY_VERSION"
poetry config --local virtualenvs.create false
poetry install

./scripts/translate.sh
