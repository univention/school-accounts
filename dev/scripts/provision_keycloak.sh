#!/bin/bash

# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

KEYCLOAK_URL=http://user-management-proxy/keycloak/

poetry -C $PROJECT_DIR/user-management-bff run keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm master \
realms add ucs \
  --realm-data $PROJECT_DIR/dev/data/realm.json || exit 1

poetry -C $PROJECT_DIR/user-management-bff run keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
users add dev univention || exit 1

poetry -C $PROJECT_DIR/user-management-bff run keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
clients add $PROJECT_DIR/appcenter-management/files/ucsschool-user-management_client_ui.json \
--override-web-origins "*" \
--override-redirect-urls "*" || exit 1

poetry -C $PROJECT_DIR/user-management-bff run keycloak-provisioning \
--username admin \
--password admin \
--url "$KEYCLOAK_URL" \
--realm ucs \
--user-realm master \
clients add $PROJECT_DIR/appcenter-management/files/ucsschool-user-management_client_bff.json \
--override-web-origins "*" \
--override-redirect-urls "*" \
--override-secret univention || exit 1
