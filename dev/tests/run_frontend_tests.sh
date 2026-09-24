#!/bin/bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Usage: run_frontend_tests.sh HOST JUNIT_FILE JUNIT_PREFIX OUTPUT_DIR

set -euo pipefail

host="$1"
junit_file="$2"
junit_prefix="$3"
output_dir="$4"

cd "$(dirname "$0")/../../user-management-bff"

apt-get update -qq
apt-get install -y -qq gettext >/dev/null
pip install --quiet --break-system-packages uv
uv sync --locked --quiet
# A no-op while the image tag in integration_tests.cfg matches uv.lock.
uv run playwright install chromium

uv run pytest -vv -m frontend \
    --base-url "https://$host" \
    --kelvin_url "$host" \
    --browser chromium \
    --screenshot only-on-failure \
    --tracing retain-on-failure \
    --output "$output_dir" \
    --junit-xml="$junit_file" \
    --junit-prefix="$junit_prefix" \
    tests/frontend
