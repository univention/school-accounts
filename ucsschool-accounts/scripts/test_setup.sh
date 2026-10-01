#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2024- 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Setup script for automated tests

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd $PROJECT_DIR

pip install --only-binary :all: uv=="$UV_VERSION"

./scripts/translate.sh
