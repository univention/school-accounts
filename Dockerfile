# Copyright (C) 2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM node:18 AS frontend_builder

COPY user-management-ui /user-management-ui
WORKDIR /user-management-ui
RUN yarn install
RUN yarn build

# Calculate Python dependencies
FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-521:latest as requirements_builder
WORKDIR /build
RUN apt-get update \
    && apt-get --assume-yes --verbose-versions --no-install-recommends install \
    python3-pip \
    && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* \
RUN rm -fv /usr/lib/python*/EXTERNALLY-MANAGED
RUN pip install poetry==1.7.1
COPY user-management-bff/pyproject.toml user-management-bff/poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --dev --without-hashes

FROM gitregistry.knut.univention.de/univention/dev/projects/ucs-base-image/ucs-base-521:latest

EXPOSE 8000

ARG commit
ARG date

LABEL "description"="UCS@school User Management API." \
    "release date"="$date" \
    "commit"="$commit"

WORKDIR /app/user-management-api

RUN apt-get update \
    && apt-get --assume-yes --verbose-versions --no-install-recommends install \
        gettext \
        python3-pip \
    && rm -fr /var/lib/apt/lists/* /var/cache/apt/archives/* \
RUN rm -fv /usr/lib/python*/EXTERNALLY-MANAGED

# Install python requirements
COPY --from=requirements_builder /build/requirements.txt .
RUN pip install --no-cache-dir -U pip wheel && pip install --no-cache-dir -r requirements.txt

# Install backend
COPY user-management-bff .
RUN pip install --no-cache-dir . && pip list
RUN ./scripts/translate.sh

# Install frontend
COPY --from=frontend_builder /user-management-ui/dist /app/frontend

COPY appcenter-management/entrypoint.d/ /entrypoint.d

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--log-level", "info", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "user_management_bff.main:app"]
