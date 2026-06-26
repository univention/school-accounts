# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Tests for the UI router (shell + interactive-login routes)."""
import pytest
from starlette.responses import RedirectResponse

from user_management_bff.adapters.authentication import NeverAuthenticatedAdapter
from user_management_bff.constants import AUTH_LOGIN_PATH, FRONTEND_PREFIX
from user_management_bff.main import app
from user_management_bff.routes import auth_port


class _StubAuth:
    """Auth adapter double exercising the route wiring without a real OIDC flow."""

    async def get_authenticated_id(self, request):
        return "dev"

    async def login_redirect(self, request, next_url=""):
        return RedirectResponse(f"https://kc/auth?next={next_url}", status_code=303)

    async def complete_login(self, request):
        return RedirectResponse(f"{FRONTEND_PREFIX}/done", status_code=303)

    async def logout(self, request):
        return RedirectResponse("https://kc/logout", status_code=303)


@pytest.fixture
def override_auth():
    def _override(adapter):
        app.dependency_overrides[auth_port] = lambda: adapter

    yield _override
    app.dependency_overrides.pop(auth_port, None)


def test_shell_renders(test_client):
    response = test_client.get(FRONTEND_PREFIX)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    # Application shell built from the design system.
    assert "<html" in body
    assert "data-theme" in body
    assert "<u-page" in body
    # Vendored assets are referenced from the static mount.
    assert "vendor/univention-design-system.js" in body
    assert "vendor/htmx.min.js" in body
    assert "vendor/alpine.min.js" in body


def test_login_route_redirects_to_idp(test_client, override_auth):
    override_auth(_StubAuth())
    response = test_client.get(
        f"{FRONTEND_PREFIX}{AUTH_LOGIN_PATH}", params={"next": "/ui/users"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "https://kc/auth?next=/ui/users"


def test_callback_route(test_client, override_auth):
    override_auth(_StubAuth())
    response = test_client.get(f"{FRONTEND_PREFIX}/auth/callback", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/done")


@pytest.mark.parametrize("method", ["get", "post"])
def test_logout_route(test_client, override_auth, method):
    override_auth(_StubAuth())
    response = getattr(test_client, method)(f"{FRONTEND_PREFIX}/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "https://kc/logout"


def test_protected_route_redirects_when_unauthenticated(test_client, override_auth):
    override_auth(NeverAuthenticatedAdapter())
    response = test_client.get(FRONTEND_PREFIX, follow_redirects=False)
    assert response.status_code == 303
    assert AUTH_LOGIN_PATH in response.headers["location"]


def test_protected_route_htmx_redirect_when_unauthenticated(test_client, override_auth):
    override_auth(NeverAuthenticatedAdapter())
    response = test_client.get(FRONTEND_PREFIX, headers={"HX-Request": "true"}, follow_redirects=False)
    assert response.status_code == 200
    assert AUTH_LOGIN_PATH in response.headers["HX-Redirect"]
