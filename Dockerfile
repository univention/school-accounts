# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Calculate Python dependencies
FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python-527:0.24.3@sha256:42db06d912f4e60c0698a4818fbf9dc2d319fc6f0e6e13992164333df47b7c59 AS backend_builder
WORKDIR /build
ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_VERSION=0.11.21
RUN apt-get update && \
    apt-get --assume-yes --verbose-versions --no-install-recommends install \
        git \
        python3-pip && \
    rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED
RUN pip install --only-binary :all: uv=="$UV_VERSION"
COPY ucsschool-accounts-bff/pyproject.toml ucsschool-accounts-bff/uv.lock ./
# Install all dependencies (prod + dev) and backend
# Currently necessary, as the integration and production tests need this
RUN uv sync --frozen --no-build --no-install-project
COPY ucsschool-accounts-bff/ ./
# Builds only this project; every dependency was installed above without building.
ARG UCSSCHOOL_ACCOUNTS_BUILD_VERSION=""
RUN uv sync --frozen --no-editable

FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-python-527:0.24.3@sha256:42db06d912f4e60c0698a4818fbf9dc2d319fc6f0e6e13992164333df47b7c59 AS runtime

EXPOSE 8000

ARG commit
ARG date

LABEL "description"="School Accounts API." \
    "release date"="$date" \
    "commit"="$commit"

WORKDIR /app/ucsschool-accounts-api

RUN apt-get update &&\
    apt-get --assume-yes --verbose-versions --no-install-recommends install \
        gettext && \
    rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    rm -fv /usr/lib/python*/EXTERNALLY-MANAGED && \
    groupadd --gid 1001 appuser && \
    useradd --gid 1001 --uid 1001 \
        --home-dir /app/ucsschool-accounts-api \
        --shell /bin/bash appuser

# Copy backend venv and src code
ENV PATH="/venv/bin:$PATH"
COPY --chown=1001:1001 --chmod=555 ucsschool-accounts-bff .
COPY --from=backend_builder --chown=1001:1001 --chmod=555 /venv /venv
RUN ./scripts/translate.sh && \
    chown -R 1001:1001 /app/ucsschool-accounts-api

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
     "ucsschool_accounts_bff.main:app"]
