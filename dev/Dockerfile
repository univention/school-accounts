# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-525:0.23.0@sha256:b256a95a43f989b24fcb2ac40b4a4524d23d4b59b6fa1b804ab7187cf7425bb3
LABEL description="Development image for ucsschool-users-management"

# The current version used in the Guardian as of 2024-03-06
ARG opa_version=0.53.0

EXPOSE 8000

ENV UV_VERSION=0.11.21

ADD https://github.com/open-policy-agent/opa/releases/download/v${opa_version}/opa_linux_amd64_static /usr/bin/opa
RUN chmod 755 /usr/bin/opa

RUN apt-get update && \
    apt-get install -y sudo \
    curl \
    gettext \
    git \
    python3-pip \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcb1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-xcb1 \
    libxcursor1 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libicu72 \
    libatomic1 \
    libxslt1.1 \
    libwoff1 \
    libevent-2.1-7 \
    libopus0 \
    libwebpdemux2 \
    libharfbuzz0b \
    libwebpmux3 \
    libwebp7 \
    libjson-glib-1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    libegl1 \
    libglx0 \
    libgudev-1.0-0 \
    libffi8 \
    libevdev2 \
    libgles2 \
    libx264-164 \
    libharfbuzz-icu0 \
    libhyphen0 \
    libasound2 && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    pip install uv==$UV_VERSION pre-commit==3.6.0 reuse==2.1.0 python-keycloak
ENV PROJECT_DIR="/src"
ENV PYTHONPYCACHEPREFIX=$PROJECT_DIR/.cache/cpython
ENV UV_CACHE_DIR=$PROJECT_DIR/.cache/uv
ENV PRE_COMMIT_HOME=$PROJECT_DIR/.cache/pre-commit-home
ENV PLAYWRIGHT_BROWSERS_PATH=$PROJECT_DIR/.cache/ms-playwright
WORKDIR $PROJECT_DIR
