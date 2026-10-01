#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

uv --project "$PROJECT_DIR/ucsschool-accounts" sync --locked --no-build --no-install-project
# Builds only this project; every dependency was installed above without building.
uv --project "$PROJECT_DIR/ucsschool-accounts" sync --locked
uv run --no-sync --no-build --project "ucsschool-accounts" playwright install
"$PROJECT_DIR/ucsschool-accounts/scripts/translate.sh"
