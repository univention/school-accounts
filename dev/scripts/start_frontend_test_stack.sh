#!/bin/bash

# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# The CI counterpart of the compose dev-server stack, next to a running Keycloak.

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export PROJECT_DIR
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080/keycloak}"
export KEYCLOAK_URL
FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:8000}"
BFF_PORT="${BFF_PORT:-8000}"
BFF_LOG="${BFF_LOG:-$PROJECT_DIR/.cache/frontend-test-bff.log}"

mkdir -p "$(dirname "$BFF_LOG")"

wait_for() {
    url="$1"
    attempts="${2:-90}"
    while [[ "$attempts" -gt 0 ]]; do
        if curl -sf -o /dev/null "$url"; then
            return 0
        fi
        attempts=$((attempts - 1))
        sleep 2
    done
    echo "Timed out waiting for $url" >&2
    return 1
}

echo "Waiting for Keycloak at $KEYCLOAK_URL"
wait_for "$KEYCLOAK_URL/realms/master/.well-known/openid-configuration"

echo "Provisioning the ucs realm"
"$PROJECT_DIR/dev/scripts/provision_keycloak.sh"

set -a
# shellcheck source=../.env.example
. "$PROJECT_DIR/dev/.env.example"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__WELL_KNOWN_URL="$KEYCLOAK_URL/realms/ucs/.well-known/openid-configuration"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__REDIRECT_URL="$FRONTEND_BASE_URL/univention/ucsschool/user-management/ui/auth/callback"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__POST_LOGOUT_REDIRECT_URL="$FRONTEND_BASE_URL/univention/ucsschool/user-management/ui"
set +a

# `.env.example` paths assume the compose bind mount at /src.
while read -r setting; do
    value="${!setting-}"
    if [[ "$value" == /src/* ]]; then
        printf -v "$setting" '%s' "$PROJECT_DIR/${value#/src/}"
    fi
done < <(sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' "$PROJECT_DIR/dev/.env.example")

echo "Starting the BFF on port $BFF_PORT, logging to $BFF_LOG"
nohup uv run --project "$PROJECT_DIR/user-management-bff" uvicorn \
    --host 0.0.0.0 \
    --port "$BFF_PORT" \
    user_management_bff.main:app \
    >"$BFF_LOG" 2>&1 &

if ! wait_for "$FRONTEND_BASE_URL/univention/ucsschool/user-management/ui/" 30; then
    cat "$BFF_LOG" >&2
    exit 1
fi
echo "Frontend test stack ready at $FRONTEND_BASE_URL"
