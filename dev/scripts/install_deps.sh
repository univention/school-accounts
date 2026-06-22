#!/bin/bash

# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

uv --project "$PROJECT_DIR/user-management-bff" sync --locked
uv run --project "user-management-bff" playwright install
OPA_UTILS=$PROJECT_DIR/.cache/opa/utils.rego
if [ ! -f "$OPA_UTILS" ]; then
  mkdir -p "$PROJECT_DIR/.cache/opa"
  curl -o "$OPA_UTILS" https://git.knut.univention.de/univention/dev/projects/authorization-engine/guardian/-/raw/main/management-api/rego_policy_bundle_template/univention/utils.rego
fi
