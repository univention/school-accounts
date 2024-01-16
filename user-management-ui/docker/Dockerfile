# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM node:18 AS builder

COPY user-management-ui /user-management-ui
WORKDIR /user-management-ui
RUN yarn install
RUN yarn build

FROM gitregistry.knut.univention.de/univention/customers/dataport/upx/container-nginx/nginx:0.1.1

ARG commit
ARG date

LABEL "description"="UCS@school User Management UI." \
    "release date"="$date" \
    "commit"="$commit"

RUN apt-get update \
    && apt-get --assume-yes --verbose-versions --no-install-recommends install \
    jq \
    && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/*
COPY --from=builder /user-management-ui/dist /app
COPY user-management-ui/docker/01-generate_config.sh /entrypoint.d/01-generate_config.sh
COPY user-management-ui/docker/nginx.conf /etc/nginx/sites-enabled/default
