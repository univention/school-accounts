#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Overridable so the CI frontend-test stack can point this at its own Keycloak
# service container, which is not behind the compose stack's proxy. The trailing
# slash is restored either way: python-keycloak joins its paths onto this string
# verbatim, so dropping it turns every request into a 404.
KEYCLOAK_URL="${KEYCLOAK_URL:-http://user-management-proxy/keycloak}"
KEYCLOAK_URL="${KEYCLOAK_URL%/}/"

uv run --project $PROJECT_DIR/user-management-bff keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm master \
realms add ucs \
--ignore-exists \
--realm-data $PROJECT_DIR/dev/data/realm.json || exit 1

uv run --project $PROJECT_DIR/user-management-bff keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
users add dev univention \
--ignore-exists || exit 1

uv run --project $PROJECT_DIR/user-management-bff keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
clients add $PROJECT_DIR/appcenter-management/files/ucsschool-user-management_client_ui.json \
--ignore-exists || exit 1

uv run --project $PROJECT_DIR/user-management-bff keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
clients modify ucsschool-user-management-ui \
--append-redirect-urls "*" \
--secret-file $PROJECT_DIR/dev/data/client.secret || exit 1
