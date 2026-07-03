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


def test_root_redirects_to_users(test_client):
    response = test_client.get(FRONTEND_PREFIX, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/users")


def test_users_list_renders_filter_form(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    # Application shell (base.html) built from the design system.
    assert "<html" in body and "data-theme" in body and "<u-page" in body
    # Fixed layout: header + filters stay put; only the results region scrolls,
    # with the table's column headers pinned.
    assert 'variant="fixed"' in body
    assert "grow scroll" in body
    assert "sticky-header" in body
    assert "vendor/univention-design-system.js" in body
    assert "vendor/htmx.min.js" in body
    assert "vendor/alpine.min.js" in body
    # Filter form: school combobox (preloaded options) wired to the cascade + search.
    assert "<u-form" in body and 'name="school"' in body
    assert "School 1" in body
    assert f"{FRONTEND_PREFIX}/users/filters" in body
    # Each field filters its own options server-side via the design system's
    # ``u-search`` event (debounced), hitting a per-field options endpoint.
    assert 'id="school-combobox"' in body
    assert f"{FRONTEND_PREFIX}/users/schools" in body
    assert f"{FRONTEND_PREFIX}/users/school-classes" in body
    assert f"{FRONTEND_PREFIX}/users/work-groups" in body
    assert 'hx-trigger="u-search delay:300ms"' in body
    # The cascade listens for the combobox's u-change now that the combobox's own
    # hx-get is spent on option search.
    assert 'hx-trigger="u-change from:#school-combobox"' in body
    # Search submits to /users and pushes the searched URL for deep-linking,
    # swapping only the results region.
    assert 'hx-push-url="true"' in body
    assert 'hx-select="#results-region"' in body
    # The cascade (school -> filters) must not inherit the form's select/push-url,
    # or its fragment response would blank out the dependent filters.
    assert 'hx-disinherit="hx-select hx-push-url"' in body
    # Empty results table (column headers only) rendered on initial load.
    assert "<u-table empty" in body


def test_users_filters_returns_options_for_school(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users/filters", params={"school": "school1"})
    assert response.status_code == 200
    body = response.text
    assert 'name="school_classes"' in body and 'name="work_groups"' in body
    assert "1a" in body and "w1a" in body
    # The dependent filters carry the selected school baked into their own hx-vals so
    # the option-search requests are not overridden by the inherited cascade hx-vals
    # (whose u-change value is absent on the multiselects' u-search event).
    assert 'school: "school1"' in body
    assert 'hx-include="#school-combobox"' not in body


def test_users_school_options_filtered_by_query(test_client):
    # Only schools whose display name contains the query come back as options.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/schools", params={"q": "Test"})
    assert response.status_code == 200
    body = response.text
    assert "<u-combobox-item" in body
    assert "Test School 1" in body
    assert ">School 1<" not in body  # plain "School 1" is filtered out


def test_users_school_options_unfiltered(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users/schools")
    assert response.status_code == 200
    assert "School 1" in response.text and "Test School 1" in response.text


def test_users_school_class_options_filtered_by_query(test_client):
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users/school-classes", params={"school": "school1", "q": "2"}
    )
    assert response.status_code == 200
    body = response.text
    assert "<u-multiselect-option" in body
    assert 'value="2b"' in body and 'value="1a"' not in body


def test_users_work_group_options_filtered_by_query(test_client):
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users/work-groups", params={"school": "school1", "q": "1"}
    )
    assert response.status_code == 200
    body = response.text
    assert 'value="w1a"' in body and 'value="w2b"' not in body


@pytest.mark.parametrize("path", ["school-classes", "work-groups"])
def test_dependent_options_empty_without_school(test_client, path):
    # Typing before a school is selected must not error; it yields no options.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/{path}", params={"q": "1"})
    assert response.status_code == 200
    assert "<u-multiselect-option" not in response.text


def test_users_search_renders_results(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"})
    assert response.status_code == 200
    body = response.text
    assert "<u-table" in body
    assert "max.muster" in body  # user1's username
    assert "Teacher (School 1)" in body  # formatted role cell
    assert "<u-badge" in body  # activated status badge
    # The searched school is preselected on the combobox (deep-link friendly).
    assert 'display-value="School 1"' in body


def test_users_deep_link_preselects_filters(test_client):
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users",
        params={"school": "school1", "school_classes": "1a", "work_groups": "w1a"},
    )
    assert response.status_code == 200
    body = response.text
    assert 'display-value="School 1"' in body
    # The deep-linked class/work-group options render preselected.
    assert 'value="1a" selected' in body
    assert 'value="w1a" selected' in body


def test_users_search_empty_state(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "NON_EXISTENT"})
    assert response.status_code == 200
    body = response.text
    assert 'slot="empty"' in body
    assert "No users found" in body


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
