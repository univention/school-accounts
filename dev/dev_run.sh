#!/bin/bash

# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

print_help () {
  cat << EOF
usage: dev_run.sh COMMAND

This scripts runs commands in the development container.
If COMMAND is 'task', special, more complicated tasks can be run.

usage: dev_run.sh task TASK

The following tasks are available:

clean: Cleans up cached files and removes docker containers and local images.
dev-server: Starts the dev server for the API.
prod-server: Starts the production docker image
cerbos-server: Starts a local Cerbos server for manually testing the policies. (currently not started with dev-server or prod-server as the adapter is not yet adjusted)
cerbos-compile: Lints and tests the Cerbos policies via \`cerbos compile\`.
sphinx: Starts the live server for the manual.
reuse: runs reuse for license annotations.
pytest: Runs the pytests for the BFF.
pytest-e2e: Runs pytest end to end tests.
translate: Generates translations for the BFF.
EOF
}

run_task() {
  TASK=$2
  if [ -z "$TASK" ]; then
    print_help
    exit 1
  fi
  echo "Running task $TASK"
  if [[ "$TASK" = "clean" ]]; then
    rm -rf .cache docs/user-management-manual/_build
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "clean-profile" \
    down \
    --remove-orphans \
    --rmi local
    exit $?
  fi
  if [[ "$TASK" = "dev-server" ]] || [[ "$TASK" = "sphinx" ]] || [[ "$TASK" = "prod-server" ]] || [[ "$TASK" = "cerbos-server" ]]; then
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "$TASK" \
    up \
    --build
    exit $?
  fi
  if [[ "$TASK" = "cerbos-compile" ]]; then
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "cerbos-server" \
    run \
    --rm \
    cerbos \
    compile /policies
    exit $?
  fi
  if [[ "$TASK" = "reuse" ]]; then
    run_command reuse annotate \
    --copyright="Univention GmbH" \
    --copyright-style=string-c \
    --license="AGPL-3.0-only" \
    --template=univention \
    --year 2024 \
    --recursive \
    --merge-copyrights \
    --skip-unrecognised \
    --skip-existing \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest" ]]; then
    run_command env --chdir=user-management-bff/ uv run \
    pytest \
    -vv \
    --cov=user_management_bff \
    --cov=keycloak_provisioning \
    -m "not e2e" $3 $4 $5 $6 $7 $8 $9  \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-e2e" ]]; then
    run_command env --chdir=user-management-bff/ uv run \
    pytest \
    -vv \
    --screenshot only-on-failure \
    --tracing retain-on-failure \
    --output "/src/.cache/test-results" \
    -m "e2e" \
    --base_url "$E2E_BASE_URL" \
    --guardian_management_url "$E2E_GUARDIAN_MANAGEMENT_URL" \
    --kelvin_url "$E2E_KELVIN_URL" \
    .
    exit $?
  fi
  if [ "$TASK" = "translate" ]; then
    run_command env ./user-management-bff/scripts/check_translations.sh
  fi
  echo "Task '$TASK' does not exist."
  exit 1
}

run_command () {
  if [ -z "$COMMAND" ]; then
    print_help
    exit 1
  fi
  DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
  -f dev/docker-compose.yaml \
  run \
  --build \
  --rm \
  -T \
  run_command "$@"
  exit $?
}

COMMAND="$1"
GITLAB_IP="$(getent -i ahostsv4 git.knut.univention.de | head -n 1 | cut -d ' ' -f 1)"
DOCKER_USER="$(id -u):$(id -g)"

if [[ ! -f "dev/.env" ]]; then
    cp dev/.env.example dev/.env
fi

if [[ "$COMMAND" = "task" ]]; then
  run_task $@
fi
if [[ "$COMMAND" = "--help" ]]; then
  print_help
  exit 0
else
  run_command $@
fi
