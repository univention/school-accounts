#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

uv --project "$PROJECT_DIR/ucsschool-accounts-bff" sync --locked
uv run --no-sync --project "ucsschool-accounts-bff" playwright install
"$PROJECT_DIR/ucsschool-accounts-bff/scripts/translate.sh"
