#!/bin/bash

# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

PROFILE="$1"
if [ -z "$PROFILE" ]
  then
    cat << EOF
usage: run_compose.sh PROFILE

This scripts starts the docker compose file included in this repo with specific profiles.
The following profiles are available:

dev-server: Starts the ui and bff service
pytest: Runs the python tests
pre-commit: Runs pre-commit
reuse: runs reuse for license annotations
sphinx: starts the live server for the manual
clean: Removes temporary data and removes all containers
clean-profile: This profile must not be chosen as it breaks the containers.
               It exists only for cleaning up by invoking the clean profile.
EOF
exit 0
fi

if [ "$PROFILE" = "clean-profile" ]; then
  echo "The clean-profile must not be invoked. It is an internal profile only."
  exit 1
fi

GITLAB_IP=$(getent -i ahostsv4 git.knut.univention.de | head -n 1 | cut -d ' ' -f 1)
DOCKER_USER="$(id -u):$(id -g)"

DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
-f dev/docker-compose.yaml \
--profile "$PROFILE" \
up \
--build

if [ "$PROFILE" = "clean" ]; then
  DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose -f dev/docker-compose.yaml --profile clean-profile down
fi
