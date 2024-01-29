# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import os

CORS_ALLOWED_ORIGINS = os.environ.get("USER_MANAGEMENT__CORS__ALLOWED_ORIGINS")
API_PREFIX = os.environ.get("USER_MANAGEMENT__API_PREFIX", "")
