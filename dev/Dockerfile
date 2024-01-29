# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM gitregistry.knut.univention.de/univention/components/ucs-base-image/ucs-base-520:latest
LABEL description="Development image for ucsschool-users-management"

EXPOSE 8000
EXPOSE 5173

RUN apt-get update && \
    apt-get install -y sudo git python3-pip nodejs npm && \
    npm install --global yarn && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    pip install poetry==1.7.1 pre-commit==3.6.0 reuse==2.1.0
ENV PROJECT_DIR "/src"
ENV PYTHONPYCACHEPREFIX $PROJECT_DIR/.cache/cpython
ENV POETRY_CACHE_DIR $PROJECT_DIR/.cache/pypoetry
ENV PRE_COMMIT_HOME $PROJECT_DIR/.cache/pre-commit-home
ENV YARN_CACHE_FOLDER $PROJECT_DIR/.cache/yarn
ENV npm_config_cache $PROJECT_DIR/.cache/npm
WORKDIR $PROJECT_DIR
