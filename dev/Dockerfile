# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-527:0.24.3@sha256:f856cd5bcb3588fd14a7d17a5da44ea58b72703b29c95720629753c66e7fde1c
LABEL description="Development image for ucsschool-users-management"

EXPOSE 8000

ENV UV_VERSION=0.11.21

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gettext \
    git \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatomic1 \
    libatspi2.0-0 \
    libcairo-gobject2 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libegl1 \
    libenchant-2-2 \
    libevdev2 \
    libevent-2.1-7 \
    libffi8 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgles2 \
    libglib2.0-0 \
    libglx0 \
    libgtk-3-0 \
    libgudev-1.0-0 \
    libharfbuzz-icu0 \
    libharfbuzz0b \
    libhyphen0 \
    libicu72 \
    libjson-glib-1.0-0 \
    libnspr4 \
    libnss3 \
    libopus0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libsecret-1-0 \
    libwebp7 \
    libwebpdemux2 \
    libwebpmux3 \
    libwoff1 \
    libx11-6 \
    libx11-xcb1 \
    libx264-164 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxslt1.1 \
    python3-pip \
    sudo && \
    rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    pip install pre-commit==3.6.0 python-keycloak reuse==2.1.0 uv=="$UV_VERSION"
ENV PROJECT_DIR="/src"
ENV PYTHONPYCACHEPREFIX=$PROJECT_DIR/.cache/cpython
ENV UV_CACHE_DIR=$PROJECT_DIR/.cache/uv
ENV PRE_COMMIT_HOME=$PROJECT_DIR/.cache/pre-commit-home
ENV PLAYWRIGHT_BROWSERS_PATH=$PROJECT_DIR/.cache/ms-playwright
WORKDIR $PROJECT_DIR
