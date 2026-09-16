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
prod-server: Starts the production docker image
cerbos-server: Starts a local Cerbos server for manually testing the policies or running CerbosPermissionsAdapter against a real PDP. (not wired into dev-server or prod-server yet, so start it separately)
cerbos-compile: Lints and tests the Cerbos policies via \`cerbos compile\`.
sphinx: Starts the live server for the manual.
reuse: runs reuse for license annotations.
pytest: Runs the pytests for the BFF.
pytest-e2e: Runs pytest end to end tests.
pytest-frontend: Runs the Playwright frontend tests against a running dev-server.
pytest-frontend-headed: Same, but in a visible browser window instead of headless.
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
    -m "not e2e and not frontend" "${@:3}" \
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
    --cerbos_url "$E2E_CERBOS_URL" \
    --kelvin_url "$E2E_KELVIN_URL" \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-frontend" ]]; then
    run_command env --chdir=user-management-bff/ uv run \
    pytest \
    -vv \
    --screenshot only-on-failure \
    --tracing retain-on-failure \
    --output "/src/.cache/frontend-test-results" \
    -m "frontend" \
    --base-url "${FRONTEND_BASE_URL:-http://user-management-proxy}" "${@:3}" \
    .
    exit $?
  fi
  if [[ "$TASK" = "pytest-frontend-headed" ]]; then
    if [[ -z "$DISPLAY" ]]; then
      echo "pytest-frontend-headed needs an X display, but DISPLAY is unset."
      echo "On Wayland, make sure Xwayland is running."
      exit 1
    fi
    # The browser runs in the container, so it needs the host's X server: the
    # socket, the address, and the cookie that authorises the connection. The
    # container shares the host's uid, so the cookie file stays readable.
    #
    # It also needs a writable HOME. The container user has none, so HOME is "/",
    # and a headed browser dies on the spot trying to build its font cache there.
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
    run_command env --chdir=user-management-bff/ uv run \
    pytest \
    -vv \
    --headed \
    --slowmo "${SLOWMO:-500}" \
    --output "/src/.cache/frontend-test-results" \
    -m "frontend" \
    --base-url "${FRONTEND_BASE_URL:-http://user-management-proxy}" "${@:3}" \
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
  "${RUN_COMMAND_ARGS[@]}" \
  run_command "$@"
  exit $?
}

COMMAND="$1"
# Extra `docker compose run` arguments a task may need, e.g. the X server the
# headed browser connects to.
RUN_COMMAND_ARGS=()
GITLAB_IP="$(getent -i ahostsv4 git.knut.univention.de | head -n 1 | cut -d ' ' -f 1)"
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
