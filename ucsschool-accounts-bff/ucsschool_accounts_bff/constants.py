# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

CORS_ALLOWED_ORIGINS = os.environ.get("UCSSCHOOL_ACCOUNTS__CORS__ALLOWED_ORIGINS")
FRONTEND_PREFIX = os.environ.get(
    "UCSSCHOOL_ACCOUNTS__FRONTEND_PREFIX", "/univention/ucsschool/ucsschool-accounts/ui"
)
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
APP_NAME = "ucsschool-accounts"

# Sources allowed to frame the UI, such as the portal, sent as `Content-Security-Policy:
# frame-ancestors`. The join script drops the `frame-ancestors 'none'` the UCS Apache
# in front of /univention/ adds, which would otherwise be sent alongside this one.
FRAME_ANCESTORS = os.environ.get("UCSSCHOOL_ACCOUNTS__FRAME_ANCESTORS") or "'self'"

# UI auth routes (relative to FRONTEND_PREFIX). The callback path must match the
# redirect URI registered for the public `-ui` Keycloak client.
AUTH_LOGIN_PATH = "/auth/login"
AUTH_CALLBACK_PATH = "/auth/callback"
AUTH_LOGOUT_PATH = "/auth/logout"

# Request header carrying the per-session CSRF token on mutating (unsafe) UI
# requests. The submit form sends it via htmx hx-headers; the server compares
# it against the token bound to the session.
CSRF_HEADER_NAME = "X-CSRF-Token"

# Selecting a whole class and resetting its password must not create a burst of
# concurrent writes against Kelvin. Bounds how many set_password calls one bulk
# submission has in flight at once.
PASSWORD_RESET_MAX_CONCURRENCY = int(
    os.environ.get("UCSSCHOOL_ACCOUNTS__PASSWORD_RESET_MAX_CONCURRENCY", "5")
)

# Number of max users/accounts that can be reset in a single password reset request
PASSWORD_RESET_MAX_TARGETS = int(os.environ.get("UCSSCHOOL_ACCOUNTS__PASSWORD_RESET_MAX_TARGETS", "200"))

# Cut-of number for listing the users in the confirmation dialog
# >5, no individual listing
PASSWORD_RESET_NAMED_LIMIT = 5

# Threshold of selected users for showing the mass action warning
# >30, mass action warning is shown
PASSWORD_RESET_BULK_THRESHOLD = 30


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


SESSION_MIDDLEWARE_SECRET = _secret_from_env("UCSSCHOOL_ACCOUNTS__SESSION_SECRET", "change-me")
SESSION_COOKIE_SECURE = os.environ.get("UCSSCHOOL_ACCOUNTS__SESSION_COOKIE_SECURE", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Scoped to the app's own routes so the session cookie - which carries the refresh and ID
# tokens - is not sent to the other applications this host serves.
SESSION_COOKIE_PATH = FRONTEND_PREFIX or "/"

LANGUAGES = ["en", "de"]

# English is the msgid language, so this default resolves without a catalog.
DEFAULT_LANGUAGE = "en"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
