#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

KEYCLOAK_URL=http://user-management-proxy/keycloak/

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
clients add $PROJECT_DIR/appcenter-management/files/ucsschool-user-management_client_ui.json || exit 1

uv run --project $PROJECT_DIR/user-management-bff keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
clients modify ucsschool-user-management-ui \
--append-redirect-urls "*" \
--secret-file $PROJECT_DIR/dev/data/client.secret || exit 1
