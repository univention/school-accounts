# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

FROM docker.software-univention.de/keycloak-keycloak:26.6.3-ucs1@sha256:c469e88a2cad9fdd087303f2747dce185d49becc08f7e594a285f51ba01d0f15

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
