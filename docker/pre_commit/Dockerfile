# Copyright (C) 2026 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

FROM gitregistry.knut.univention.de/univention/dev/tooling/ci-components/uv@sha256:62d1e485c3a3825c72293d18158f6281fa5421572d23266668e8a720a7ecfa85

ENV PYTHONUNBUFFERED=1
ENV PIPX_HOME="/opt/pipx"
ENV PIPX_BIN_DIR="/usr/local/bin"

ARG UID=1000
ARG GID=1000
ARG BASEDPYRIGHT_VERSION=1.39.8

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential git pipx python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pipx install "basedpyright==${BASEDPYRIGHT_VERSION}" && \
    groupadd --gid "${GID}" precommit && \
    useradd --create-home --shell /bin/bash --uid "${UID}" --gid "${GID}" precommit

USER precommit
WORKDIR /src
