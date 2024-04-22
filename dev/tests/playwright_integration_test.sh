#!/bin/bash
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

cd /user-management/user-management-ui || exit 1
corepack enable
corepack install
yarn install
yarn test:e2e:setup
PLAYWRIGHT_JUNIT_OUTPUT_NAME="results.xml" CI="true" CI_INTEGRATION="true" PLAYWRIGHT_TEST_BASE_URL="https://$1" yarn test:e2e --reporter=junit,html
PLAYWRIGHT_JUNIT_OUTPUT_NAME="results.xml" PLAYWRIGHT_TEST_BASE_URL="https://$1" /user-management/dev/tests/playwright2gitlab_junit.py
