# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import os

CORS_ALLOWED_ORIGINS = os.environ.get("USER_MANAGEMENT__CORS__ALLOWED_ORIGINS")
API_PREFIX = os.environ.get("USER_MANAGEMENT__API_PREFIX", "/univention/ucsschool/user-management/bff")
FRONTEND_PREFIX = os.environ.get(
    "USER_MANAGEMENT__FRONTEND_PREFIX", "/univention/ucsschool/user-management/ui"
)
FRONTEND_DIR = os.environ.get("USER_MANAGEMENT__FRONTEND_DIR", "/app/frontend")
APP_NAME = "ucsschool-user-management"
NAMESPACE_NAME = "user-management"

LANGUAGES = ["en", "de"]
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
