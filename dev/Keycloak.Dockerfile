# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

FROM artifacts.software-univention.de/nubus/images/keycloak:26.7.4-nubus2@sha256:6a4a2da058ae28dce96c8b43663dd5faf2a0f1b290cc0c5e688156c6681bb5f4
USER 1000

# Configure a database vendor. Problem with dev-mem, set to default dev-file
ENV KC_DB=dev-file

# relative path needs to be set in build stage
ENV KC_HTTP_RELATIVE_PATH=/keycloak
# Enable health and metrics support
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true


WORKDIR /opt/keycloak

# admin credentials
ENV KEYCLOAK_ADMIN=admin
ENV KEYCLOAK_ADMIN_PASSWORD=admin

# configuring keycloak
ENV KC_HOSTNAME=ucsschool-accounts-proxy
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY=edge
ENV KC_HOSTNAME_STRICT_HTTPS=false
ENV KC_LOG_LEVEL=INFO
