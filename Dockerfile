# Copyright (C) 2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

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
RUN uv sync --frozen --no-editable

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
        --shell /bin/bash appuser

# Copy backend venv and src code
ENV PATH="/venv/bin:$PATH"
COPY --chown=1001:1001 --chmod=555 user-management-bff .
COPY --from=backend_builder --chown=1001:1001 --chmod=555 /venv /venv
RUN ./scripts/translate.sh && \
    chown -R 1001:1001 /app/user-management-api

COPY appcenter-management/entrypoint.d/ /entrypoint.d

# Same as the base image's default entrypoint:
# tini is required as PID 1 so it forwards signals through the runuser hop
# below.
ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
# --no-control-socket: gunicorn has no write permissions in the workdir, so
# it logs a permission error when trying to create the control socket
# directory otherwise.
# drop privileges and start app as unprivileged user
CMD ["runuser", "-u", "appuser", "--", "gunicorn", \
     "--log-level", "info", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--no-control-socket", \
     "user_management_bff.main:app"]
