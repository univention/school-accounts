#!/bin/bash

# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Brings up everything the frontend tests need, for a runner that has a Keycloak
# reachable but nothing else: provisions the realm, starts the BFF against the
# File adapters and the dev fixture data, and returns once both answer.
#
# Locally the compose dev-server profile already provides this stack, so this is
# the CI entry point rather than a second way to develop against.

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

# The adapter selection and the fixture data are the same ones the compose dev
# stack runs on, so the tests see one deployment shape rather than two. Only the
# paths and the URLs the browser has to reach differ from `.env.example`.
set -a
# shellcheck source=../.env.example
. "$PROJECT_DIR/dev/.env.example"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__WELL_KNOWN_URL="$KEYCLOAK_URL/realms/ucs/.well-known/openid-configuration"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__REDIRECT_URL="$FRONTEND_BASE_URL/univention/ucsschool/user-management/ui/auth/callback"
COOKIE_SESSION_AUTHENTICATION_ADAPTER__POST_LOGOUT_REDIRECT_URL="$FRONTEND_BASE_URL/univention/ucsschool/user-management/ui"
set +a

# `.env.example` is written for the compose stack, which bind-mounts the repo at
# /src; here the checkout is wherever CI put it, so every path it holds has to
# move with it. Rewriting the prefix beats listing the variables, which is what
# this did until a confidential client secret was added upstream and the job
# failed on a setting it had never heard of.
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
