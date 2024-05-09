#!/bin/bash
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

cd /user-management/dev/tests/product-tests || exit 1
pip install poetry
poetry install --no-root
CI="true" CI_INTEGRATION="true" poetry run pytest --reruns 3 --reruns-delay 3 --base-url "https://$1" --kelvin_url="primary.school.test"  --browser firefox --browser webkit --browser chromium --tracing retain-on-failure --junit-xml="$2" --junit-prefix="$3"
