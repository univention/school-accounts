#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

uv --project "$PROJECT_DIR/user-management-bff" sync --locked
uv run --project "user-management-bff" playwright install
"$PROJECT_DIR/user-management-bff/scripts/translate.sh"
