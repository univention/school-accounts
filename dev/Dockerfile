# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-520:latest
LABEL description="Development image for ucsschool-users-management"

EXPOSE 8000
EXPOSE 5173

RUN apt-get update && \
    apt-get install -y sudo \
    git \
    python3-pip \
    nodejs \
    npm \
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
    libasound2 && \
    npm install --global yarn && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    pip install poetry==1.7.1 pre-commit==3.6.0 reuse==2.1.0 python-keycloak
ENV PROJECT_DIR "/src"
ENV PYTHONPYCACHEPREFIX $PROJECT_DIR/.cache/cpython
ENV POETRY_CACHE_DIR $PROJECT_DIR/.cache/pypoetry
ENV PRE_COMMIT_HOME $PROJECT_DIR/.cache/pre-commit-home
ENV YARN_CACHE_FOLDER $PROJECT_DIR/.cache/yarn
ENV npm_config_cache $PROJECT_DIR/.cache/npm
ENV PLAYWRIGHT_BROWSERS_PATH $PROJECT_DIR/.cache/ms-playwright
WORKDIR $PROJECT_DIR
