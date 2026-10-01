#!/usr/bin/env bash

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
kelvin-server: Starts the dev server against a real Kelvin and a local Cerbos, with no interactive login. Configured by dev/.env.kelvin.
prod-server: Starts the production docker image
cerbos-server: Starts a local Cerbos server for manually testing the policies or running CerbosPermissionsAdapter against a real PDP. (not wired into dev-server or prod-server yet, so start it separately)
cerbos-compile: Lints and tests the Cerbos policies via \`cerbos compile\`.
sphinx: Starts the live server for the manual.
reuse: runs reuse for license annotations.
pytest: Runs the pytests for the app.
pytest-e2e: Runs pytest end to end tests.
pytest-frontend: Runs the Playwright frontend tests against a running dev-server.
pytest-frontend-headed: Same, but in a visible browser window instead of headless.
translate: Generates translations for the app.
EOF
}

run_task() {
  TASK=$2
  if [[ -z "$TASK" ]]; then
    print_help
    exit 1
  fi
  echo "Running task $TASK"
  if [[ "$TASK" = "clean" ]]; then
    rm -rf .cache docs/ucsschool-accounts/_build
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "clean-profile" \
    down \
    --remove-orphans \
    --rmi local
    exit $?
  fi
  if [[ "$TASK" = "kelvin-server" ]]; then
    prepare_kelvin_env
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP \
    UCS_PRIMARY_HOST=$UCS_PRIMARY_HOST UCS_PRIMARY_IP=$UCS_PRIMARY_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "kelvin-server" \
    up \
    --build
    exit $?
  fi
  if [[ "$TASK" = "dev-server" ]] || [[ "$TASK" = "sphinx" ]] || [[ "$TASK" = "prod-server" ]] || [[ "$TASK" = "cerbos-server" ]]; then
    DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
    -f dev/docker-compose.yaml \
    --profile "$TASK" \
    up \
    --build "${@:3}"
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
    run_command env --chdir=ucsschool-accounts/ uv run \
    pytest \
    -vv \
    --cov=ucsschool_accounts \
    --cov=keycloak_provisioning \
    -m "not e2e and not frontend" "${@:3}" \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-e2e" ]]; then
    run_command env --chdir=ucsschool-accounts/ uv run \
    pytest \
    -vv \
    --screenshot only-on-failure \
    --tracing retain-on-failure \
    --output "/src/.cache/test-results" \
    -m "e2e" \
    --base_url "$E2E_BASE_URL" \
    --cerbos_url "$E2E_CERBOS_URL" \
    --kelvin_url "$E2E_KELVIN_URL" \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-frontend" ]]; then
    run_command env --chdir=ucsschool-accounts/ uv run \
    pytest \
    -vv \
    --screenshot only-on-failure \
    --tracing retain-on-failure \
    --output "/src/.cache/frontend-test-results" \
    -m "frontend" \
    --base-url "${FRONTEND_BASE_URL:-http://ucsschool-accounts-proxy}" "${@:3}" \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-frontend-headed" ]]; then
    if [[ -z "$DISPLAY" ]]; then
      echo "pytest-frontend-headed needs an X display, but DISPLAY is unset."
      echo "On Wayland, make sure Xwayland is running."
      exit 1
    fi
    # Chromium dies building its font cache without a writable HOME.
    mkdir -p .cache/browser-home
    RUN_COMMAND_ARGS=(
      -e "DISPLAY=$DISPLAY"
      -e "HOME=/src/.cache/browser-home"
      -v /tmp/.X11-unix:/tmp/.X11-unix:ro
    )
    if [[ -n "$XAUTHORITY" ]]; then
      RUN_COMMAND_ARGS+=(-e "XAUTHORITY=$XAUTHORITY" -v "$XAUTHORITY:$XAUTHORITY:ro")
    fi
    if [[ -n "$PWDEBUG" ]]; then
      RUN_COMMAND_ARGS+=(-e "PWDEBUG=$PWDEBUG")
    fi
    run_command env --chdir=ucsschool-accounts/ uv run \
    pytest \
    -vv \
    --headed \
    --slowmo "${SLOWMO:-500}" \
    --output "/src/.cache/frontend-test-results" \
    -m "frontend" \
    --base-url "${FRONTEND_BASE_URL:-http://ucsschool-accounts-proxy}" "${@:3}" \
    .
    exit $?
  fi
  if [[ "$TASK" = "translate" ]]; then
    run_command env ./ucsschool-accounts/scripts/check_translations.sh
  fi
  echo "Task '$TASK' does not exist."
  exit 1
}

# The container resolves neither the host's /etc/hosts nor, reliably, a DNS zone
# holding the UCS names, and every instance mints its own root CA. Both are read
# off the one host dev/.env.kelvin names, so there is a single place to change.
prepare_kelvin_env () {
  if [[ ! -f "dev/.env.kelvin" ]]; then
    cp dev/.env.kelvin.example dev/.env.kelvin
    echo "Wrote dev/.env.kelvin from the example."
    echo "Set the host, the credentials and ALWAYS_AUTHENTICATED_ADAPTER__ACTOR_ID"
    echo "in it - the actor has to be a UCS@school user - then run this again."
    exit 1
  fi
  UCS_PRIMARY_HOST="$(sed -n 's/^KELVIN_PERSISTENCE_ADAPTER__URL=//p' dev/.env.kelvin \
    | tail -n 1 | tr -d '\r\042\047')"
  if [[ -z "$UCS_PRIMARY_HOST" ]]; then
    echo "dev/.env.kelvin sets no KELVIN_PERSISTENCE_ADAPTER__URL."
    exit 1
  fi
  UCS_PRIMARY_IP="$(getent -i ahostsv4 "$UCS_PRIMARY_HOST" | head -n 1 | cut -d ' ' -f 1)"
  if [[ -z "$UCS_PRIMARY_IP" ]]; then
    echo "Cannot resolve $UCS_PRIMARY_HOST. Add it to /etc/hosts or fix the name"
    echo "in dev/.env.kelvin; the container is given the address, not the name."
    exit 1
  fi
  echo "Kelvin: $UCS_PRIMARY_HOST ($UCS_PRIMARY_IP)"
  if [[ ! -f "dev/local/ca-bundle.crt" ]]; then
    dev/scripts/fetch_ucs_ca.sh "$UCS_PRIMARY_HOST"
  fi
  return 0
}

run_command () {
  if [[ -z "$COMMAND" ]]; then
    print_help
    exit 1
  fi
  DOCKER_USER=$DOCKER_USER GITLAB_IP=$GITLAB_IP docker compose \
  -f dev/docker-compose.yaml \
  run \
  --build \
  --rm \
  -T \
  "${RUN_COMMAND_ARGS[@]}" \
  run_command "$@"
  exit $?
}

COMMAND="$1"
RUN_COMMAND_ARGS=()
GITLAB_IP="$(getent -i ahostsv4 git.knut.univention.de | head -n 1 | cut -d ' ' -f 1)"
if [[ -z "$GITLAB_IP" ]]; then
  # Every service pins this name to an address, so an empty one reaches docker as
  # `--add-host git.knut.univention.de:` and it answers "invalid IP address in
  # add-host", which says nothing about the VPN being down.
  echo "Cannot resolve git.knut.univention.de - is the VPN up?"
  exit 1
fi
DOCKER_USER="$(id -u):$(id -g)"

if [[ ! -f "dev/.env" ]]; then
    cp dev/.env.example dev/.env
fi

if [[ "$COMMAND" = "task" ]]; then
  run_task "$@"
fi
if [[ "$COMMAND" = "--help" ]]; then
  print_help
  exit 0
else
  run_command $@
fi
