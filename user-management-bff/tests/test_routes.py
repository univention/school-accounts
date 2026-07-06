# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Tests for the UI router (shell + interactive-login routes)."""
import pytest
from starlette.responses import RedirectResponse

from user_management_bff.adapters.authentication import NeverAuthenticatedAdapter
from user_management_bff.adapters.permissions import FilePermissionsAdapter
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
    # The design-system stylesheet is a render-blocking <link> carrying the marker
    # attribute (prevents the flash of unstyled content; module skips self-injection).
    assert 'rel="stylesheet" href="' in body and "vendor/univention-design-system.css" in body
    assert "data-univention-design-system" in body
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


def test_users_list_links_username_to_detail(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"})
    body = response.text
    # The username cell is a link into the detail view carrying the school context.
    assert f'<u-link href="{FRONTEND_PREFIX}/users/user1?school=school1"' in body


# ---------------------------------------------------------------------------
# Detail / edit view
# ---------------------------------------------------------------------------
def test_user_detail_renders_combined_view(test_client):
    response = test_client.get(f"{FRONTEND_PREFIX}/users/user1", params={"school": "school1"})
    assert response.status_code == 200
    body = response.text
    assert "<u-page" in body  # full page shell
    # Heading built from the readable name parts.
    assert "Max Mustermann" in body
    # A single u-form patches the user in place (combined detail/edit view).
    assert f'hx-patch="{FRONTEND_PREFIX}/users/user1?school=school1"' in body
    assert 'hx-target="#user-detail"' in body
    # The dev actor can write, so editable controls + a Save button are shown.
    assert 'name="last_name"' in body
    assert "Save" in body
    # A password control appears only because it is writable (write-only attribute).
    assert 'type="password"' in body
    # Relational attributes render read-only as formatted display names.
    assert "Teacher (School 1)" in body


def test_user_detail_unknown_school_is_not_found(test_client):
    # A stale deep link to a school the user does not belong to -> 404 message page.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/user1", params={"school": "school4"})
    assert response.status_code == 404
    assert "Object not found" in response.text


def test_user_patch_success_redirects_to_list(test_client):
    response = test_client.patch(
        f"{FRONTEND_PREFIX}/users/user1",
        params={"school": "school1"},
        data={
            "last_name": "Neumann",
            "first_name": "Max",
            "email": "max@example.com",
            "birthday": "2010-05-04",
            "password": "s3cret-pw",
            # The checkbox submits a single value via its unchecked-value.
            "activated": "true",
        },
    )
    # On success htmx is told to navigate back to the school-scoped list.
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"{FRONTEND_PREFIX}/users?school=school1"


def test_user_patch_deactivate_without_activated_key(test_client):
    # No "activated" field submitted at all (exercises the absent-checkbox branch);
    # patching only a single writable scalar still succeeds.
    response = test_client.patch(
        f"{FRONTEND_PREFIX}/users/user1",
        params={"school": "school1"},
        data={"first_name": "Maximilian"},
    )
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"{FRONTEND_PREFIX}/users?school=school1"


def test_user_patch_invalid_date_shows_inline_error(test_client):
    response = test_client.patch(
        f"{FRONTEND_PREFIX}/users/user1",
        params={"school": "school1"},
        data={"last_name": "Mustermann", "birthday": "not-a-date"},
    )
    # Handled inline: the card is re-rendered (200) with the field flagged and the
    # submitted value preserved, rather than bubbling a generic error.
    assert response.status_code == 200
    body = response.text
    assert "error=" in body
    assert "not-a-date" in body


class _CsrfRejectAuth:
    """Authenticated actor whose CSRF check always fails (exercises the reject branch)."""

    async def get_authenticated_id(self, request):
        return "dev"

    async def issue_csrf_token(self, request):
        return "tok"

    async def check_csrf(self, request, submitted):
        return False


def test_user_patch_rejects_missing_csrf_token(test_client, override_auth):
    override_auth(_CsrfRejectAuth())
    response = test_client.patch(
        f"{FRONTEND_PREFIX}/users/user1",
        params={"school": "school1"},
        data={"first_name": "Nope"},
    )
    assert response.status_code == 403
    assert "security token" in response.text.lower()


def test_user_patch_permission_denied(test_client, mocker):
    # Actor holds no write permission on the target -> PermissionsError -> 403 page.
    mocker.patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
    response = test_client.patch(
        f"{FRONTEND_PREFIX}/users/user1",
        params={"school": "school1"},
        data={"first_name": "Nope"},
    )
    assert response.status_code == 403
    assert "permission" in response.text.lower()


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
