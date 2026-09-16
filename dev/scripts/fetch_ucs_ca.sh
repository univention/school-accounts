#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -euo pipefail

HOST="${1:-primary.ucsschool.test}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="$REPO_ROOT/dev/local/ucs-root-ca.crt"
BUNDLE="$REPO_ROOT/dev/local/ca-bundle.crt"

mkdir -p "$REPO_ROOT/dev/local"
curl -fsS -o "$TARGET" "http://$HOST/ucs-root-ca.crt"

system_roots() {
    local candidate
    for candidate in /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt; do
        if [ -r "$candidate" ]; then
            echo "$candidate"
            return
        fi
    done
    python3 -c 'import certifi; print(certifi.where())'
}

# SSL_CERT_FILE and REQUESTS_CA_BUNDLE replace the trust store rather than adding to
# it, so anything pointed at the UCS root alone stops trusting the public roots and
# can no longer reach PyPI. The bundle carries both.
cat "$(system_roots)" "$TARGET" > "$BUNDLE"

# Every UCS instance mints its own root CA, so a certificate kept from an earlier
# environment fails verification with no hint that it is the wrong one.
openssl x509 -in "$TARGET" -noout -subject -enddate
echo "Written to $TARGET and $BUNDLE"
