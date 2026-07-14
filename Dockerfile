# Copyright (C) 2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM node:18.20.8 AS frontend_builder

COPY user-management-ui /user-management-ui
WORKDIR /user-management-ui
RUN yarn install
RUN yarn build

# Calculate Python dependencies
FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python-525:0.23.0@sha256:afd982bfba8077a08a873e0e2c567dbc9b2c8e943eefac68b1d06a784b0f1859 AS backend_builder
WORKDIR /build
ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_VERSION=0.11.21
RUN apt-get update && \
    apt-get --assume-yes --verbose-versions --no-install-recommends install python3-pip && \
    rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED
RUN pip install uv=="$UV_VERSION"
COPY user-management-bff/pyproject.toml user-management-bff/uv.lock ./
# Install all dependencies (prod + dev) and backend
# Currently necessary, as the integration and production tests need this
RUN uv sync --frozen --no-install-project
COPY user-management-bff/ ./
RUN uv sync --frozen

FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python-525:0.23.0@sha256:afd982bfba8077a08a873e0e2c567dbc9b2c8e943eefac68b1d06a784b0f1859 AS runtime

EXPOSE 8000

ARG commit
ARG date

LABEL "description"="UCS@school User Management API." \
    "release date"="$date" \
    "commit"="$commit"

WORKDIR /app/user-management-api

RUN apt-get update &&\
    apt-get --assume-yes --verbose-versions --no-install-recommends install \
        gettext && \
    rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    groupadd --gid 1001 appuser && \
    useradd --gid 1001 --uid 1001 \
        --home-dir /app/user-management-api \
        --shell /bin/bash appuser && \
    passwd -d appuser

# Copy backend venv and src code
ENV PATH="/venv/bin:$PATH"
COPY --chown=1001:1001 --chmod=555 user-management-bff .
COPY --from=backend_builder --chown=1001:1001 --chmod=555 /venv /venv
# Install frontend
COPY --from=frontend_builder --chown=1001:1001 --chmod=555 /user-management-ui/dist /app/frontend
RUN ./scripts/translate.sh && \
    chown -R 1001:1001 /app/user-management-api && \
    chown -R 1001:1001 /app/frontend

COPY --chmod=555 appcenter-management/entrypoint.d/ /entrypoint.d
# had to be added as the entrypoint runs as user appuser (1001:1001)
RUN touch /etc/machine.user && chown 1001:1001 /etc/machine.user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--log-level", "info", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "user_management_bff.main:app"]
USER 1001:1001
