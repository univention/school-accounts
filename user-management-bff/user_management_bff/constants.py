# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

CORS_ALLOWED_ORIGINS = os.environ.get("USER_MANAGEMENT__CORS__ALLOWED_ORIGINS")
FRONTEND_PREFIX = os.environ.get(
    "USER_MANAGEMENT__FRONTEND_PREFIX", "/univention/ucsschool/user-management/ui"
)
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
APP_NAME = "ucsschool-user-management"
NAMESPACE_NAME = "user-management"

# UI auth routes (relative to FRONTEND_PREFIX). The callback path must match the
# redirect URI registered for the public `-ui` Keycloak client.
AUTH_LOGIN_PATH = "/auth/login"
AUTH_CALLBACK_PATH = "/auth/callback"
AUTH_LOGOUT_PATH = "/auth/logout"


# Secret for Starlette's SessionMiddleware, which holds the transient OAuth
# state (CSRF `state` + PKCE `code_verifier`) between the login redirect and the
# callback. This is distinct from the authenticated session cookie. The `_FILE`
# variant (deployment-provisioned secret file) takes precedence, mirroring the
# Kelvin/Guardian secret-file convention.
def _secret_from_env(name: str, default: str) -> str:
    file_path = os.environ.get(f"{name}_FILE")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fd:
            return fd.read().strip()
    return os.environ.get(name, default)


SESSION_MIDDLEWARE_SECRET = _secret_from_env("USER_MANAGEMENT__SESSION_SECRET", "change-me")
SESSION_COOKIE_SECURE = os.environ.get("USER_MANAGEMENT__SESSION_COOKIE_SECURE", "true").lower() in (
    "1",
    "true",
    "yes",
)

LANGUAGES = ["en", "de"]
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
