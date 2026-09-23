#!/bin/bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Runs the frontend tests against a UCS system, from inside a Playwright image.
# Its tag in `integration_tests.cfg` should match the locked playwright version,
# so the browsers it ships are the ones the library looks for.
# `integration_tests.cfg` starts it on the primary against the primary itself;
# given --kelvin_url, the suite seeds its own test data there.
#
# Usage: run_frontend_tests.sh HOST JUNIT_FILE JUNIT_PREFIX OUTPUT_DIR

set -euo pipefail

host="$1"
junit_file="$2"
junit_prefix="$3"
output_dir="$4"

cd "$(dirname "$0")/../../user-management-bff"

# The session conftest compiles the translation catalogs with msgfmt.
apt-get update -qq
apt-get install -y -qq gettext >/dev/null
pip install --quiet --break-system-packages uv
uv sync --locked --quiet
# A no-op while the image tag matches uv.lock. After a playwright bump that the
# tag did not follow, it fetches the browsers the locked version expects
# instead of failing every test on a missing executable.
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
