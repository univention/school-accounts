#!/bin/bash
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail

# /etc/machine.secret is injected by the appcenter sometime after the
# container starts; there's no guarantee it's already there at boot.
TIMEOUT="${APPCENTER_WAIT_TIMEOUT:-60}"
elapsed=0
while [[ ! -f /etc/machine.secret ]]; do
    if [[ "$elapsed" -ge "$TIMEOUT" ]]; then
        echo "ERROR: timed out waiting for /etc/machine.secret after ${TIMEOUT}s" >&2
        exit 1
    fi
    echo "waiting for /etc/machine.secret (${elapsed}s / ${TIMEOUT}s)" >&2
    sleep 1
    elapsed=$((elapsed + 1))
done

# 711: root keeps full access, everyone else can traverse to a known file
# but not list the directory's contents.
mkdir -p -m 711 /run/secrets

# set read permissions for appuser
install -m 400 -o appuser -g appuser /etc/machine.secret /run/secrets/machine.secret
install -m 400 -o appuser -g appuser /etc/machine.user /run/secrets/machine.user

CLIENT_SECRET=/var/lib/univention-appcenter/apps/ucsschool-user-management/conf/client.secret
if [[ -f "$CLIENT_SECRET" ]]; then
    # set read permissions for appuser
    install -m 400 -o appuser -g appuser "$CLIENT_SECRET" /run/secrets/client.secret
fi
