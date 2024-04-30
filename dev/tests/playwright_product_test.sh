#!/bin/bash
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

cd /user-management/dev/tests/product-tests || exit 1
pip install poetry
poetry install --no-root
CI="true" CI_INTEGRATION="true" poetry run pytest --base-url "https://$1" --browser firefox --browser webkit --browser chromium --junit-xml="$2" --junit-prefix="$3"
