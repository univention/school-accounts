#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

HOST="${1:-primary.ucsschool.test}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="$REPO_ROOT/dev/local/ucs-root-ca.crt"

mkdir -p "$REPO_ROOT/dev/local"
curl -fsS -o "$TARGET" "http://$HOST/ucs-root-ca.crt"

# Every UCS instance mints its own root CA, so a certificate kept from an earlier
# environment fails verification with no hint that it is the wrong one.
openssl x509 -in "$TARGET" -noout -subject -enddate
echo "Written to $TARGET"
