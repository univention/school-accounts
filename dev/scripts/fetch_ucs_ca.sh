#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

HOST="${1:-primary.ucsschool.test}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="$REPO_ROOT/dev/local/ucs-root-ca.crt"
BUNDLE="$REPO_ROOT/dev/local/ca-bundle.crt"

mkdir -p "$REPO_ROOT/dev/local"
# Unverified because the certificate that would verify it is the one being fetched.
curl -fsS --insecure -o "$TARGET" "https://$HOST/ucs-root-ca.crt"

system_roots() {
    local candidate
    for candidate in /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt; do
        if [[ -r "$candidate" ]]; then
            echo "$candidate"
            return
        fi
    done
    python3 -c 'import certifi; print(certifi.where())'
}

# SSL_CERT_FILE and REQUESTS_CA_BUNDLE replace the trust store instead of adding to it,
# so the bundle has to carry the public roots or PyPI stops verifying.
cat "$(system_roots)" "$TARGET" > "$BUNDLE"

# Every instance mints its own root CA, and a stale one fails verification without saying so.
openssl x509 -in "$TARGET" -noout -subject -enddate
echo "Written to $TARGET and $BUNDLE"
