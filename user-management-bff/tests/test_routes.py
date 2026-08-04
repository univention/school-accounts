# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Tests for the UI router (shell + interactive-login routes)."""
import sys
from typing import Any, Callable, Coroutine, Generator

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from user_management_bff.adapters.authentication import NeverAuthenticatedAdapter
from user_management_bff.constants import AUTH_LOGIN_PATH, FRONTEND_PREFIX
from user_management_bff.main import app
from user_management_bff.ports import FastAPIAuthenticationPort
from user_management_bff.routes import auth_port

if sys.version_info >= (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


class _StubAuth(FastAPIAuthenticationPort):
    """Auth adapter double exercising the route wiring without a real OIDC flow."""

    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep(request: Request) -> str:
            return await self.get_authenticated_id(request)

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        return "dev"

    @override
    async def login_redirect(self, request: Request, next_url: str = "") -> Response:
        return RedirectResponse(f"https://kc/auth?next={next_url}", status_code=303)

    @override
    async def complete_login(self, request: Request) -> Response:
        return RedirectResponse(f"{FRONTEND_PREFIX}/done", status_code=303)

    @override
    async def logout(self, request: Request) -> Response:
        return RedirectResponse("https://kc/logout", status_code=303)


@pytest.fixture
def override_auth() -> Generator[Callable[[FastAPIAuthenticationPort], None], None, None]:
    def _override(adapter: FastAPIAuthenticationPort) -> None:
        app.dependency_overrides[auth_port] = lambda: adapter

    yield _override
    app.dependency_overrides.pop(auth_port, None)


def test_root_redirects_to_users(test_client: TestClient):
    response = test_client.get(FRONTEND_PREFIX, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/users")


def test_users_list_renders_filter_form(test_client: TestClient):
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
    # Filter sidebar: school list select (preloaded items) wired to the cascade + search.
    assert "<u-form" in body and 'name="school"' in body
    assert "<u-list-select" in body
    assert "School 1" in body
    assert f"{FRONTEND_PREFIX}/users/filters" in body
    # Classes and work groups share one control, so there is a single dependent
    # options endpoint rather than one per dataset.
    assert 'name="group"' in body
    # Each list filters its own items server-side via the design system's
    # ``u-search`` event (debounced), hitting its own options endpoint.
    assert 'id="school-list"' in body
    assert f"{FRONTEND_PREFIX}/users/schools" in body
    assert f"{FRONTEND_PREFIX}/users/groups" in body
    assert 'hx-trigger="u-search delay:300ms"' in body
    # The cascade listens for the school list's u-change now that its own hx-get
    # is spent on item search.
    assert 'hx-trigger="u-change from:#school-list"' in body
    # Sidebar next to the results column, both stretched to full height.
    assert 'align="stretch"' in body and 'basis="sm"' in body
    # Changing either list searches immediately; there is no submit button.
    assert 'hx-trigger="u-change delay:100ms"' in body
    assert 'type="submit"' not in body
    # The combined list carries an explicit reset option, preselected while no
    # class or work group is chosen.
    assert 'value="all" selected' in body
    assert "All classes and work groups" in body
    # Search submits to /users and pushes the searched URL for deep-linking,
    # swapping only the results region.
    assert 'hx-push-url="true"' in body
    assert 'hx-select="#results-region"' in body
    # The cascade (school -> filters) must not inherit the form's select/push-url,
    # or its fragment response would blank out the dependent filters.
    assert 'hx-disinherit="hx-select hx-push-url"' in body
    # Empty results table (column headers only) rendered on initial load.
    assert "<u-table empty" in body


def test_users_filters_returns_combined_control_for_school(test_client: TestClient):
    response = test_client.get(f"{FRONTEND_PREFIX}/users/filters", params={"school": "school1"})
    assert response.status_code == 200
    body = response.text
    # The cascade returns the whole control, not just its items, so that switching
    # school drops the previous selection the element was holding.
    assert "<u-list-select" in body and 'name="group"' in body
    # Both datasets arrive as labelled groups of one single-select list, behind
    # the reset option, which a fresh school starts on.
    assert body.count("<u-list-select-group") == 2
    assert 'value="school_class:1a"' in body and 'value="work_group:w1a"' in body
    assert 'value="all" selected' in body
    # The control carries the selected school baked into its own hx-vals so the
    # item-search requests are not overridden by the inherited cascade hx-vals
    # (whose u-change value is absent on the list select's u-search event).
    assert 'school: "school1"' in body
    assert "hx-include=" not in body


def test_users_school_options_filtered_by_query(test_client: TestClient):
    # Only schools whose display name contains the query come back as options.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/schools", params={"q": "Test"})
    assert response.status_code == 200
    body = response.text
    assert "<u-list-select-item" in body
    assert "Test School 1" in body
    assert ">School 1<" not in body  # plain "School 1" is filtered out


def test_users_school_options_unfiltered(test_client: TestClient):
    response = test_client.get(f"{FRONTEND_PREFIX}/users/schools")
    assert response.status_code == 200
    assert "School 1" in response.text and "Test School 1" in response.text


def test_users_group_options_filtered_by_query(test_client: TestClient):
    # One query filters both datasets; each surviving value keeps its kind prefix.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/groups", params={"school": "school1", "q": "2"})
    assert response.status_code == 200
    body = response.text
    assert "<u-list-select-group" in body
    assert 'value="school_class:2b"' in body and 'value="school_class:1a"' not in body
    assert 'value="work_group:w2b"' in body and 'value="work_group:w1a"' not in body


def test_users_group_options_omit_empty_sections(test_client: TestClient):
    # A query matching only work groups must not leave an empty classes heading.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/groups", params={"school": "school1", "q": "w"})
    assert response.status_code == 200
    body = response.text
    assert body.count("<u-list-select-group") == 1
    assert 'value="work_group:w1a"' in body and "school_class:" not in body


def test_users_group_options_hide_reset_while_filtering(test_client: TestClient):
    # The reset option would otherwise keep the list non-empty for every query,
    # so a search with no matches could never reach the empty state.
    filtered = test_client.get(f"{FRONTEND_PREFIX}/users/groups", params={"school": "school1", "q": "w"})
    assert 'value="all"' not in filtered.text
    unfiltered = test_client.get(f"{FRONTEND_PREFIX}/users/groups", params={"school": "school1"})
    assert 'value="all"' in unfiltered.text


def test_group_options_empty_without_school(test_client: TestClient):
    # Typing before a school is selected must not error; it yields no options.
    response = test_client.get(f"{FRONTEND_PREFIX}/users/groups", params={"q": "1"})
    assert response.status_code == 200
    body = response.text
    assert "<u-list-select-item" not in body
    assert "Select a school first" in body


def test_users_search_renders_results(test_client: TestClient):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"})
    assert response.status_code == 200
    body = response.text
    assert "<u-table" in body
    assert "max.muster" in body  # user1's username
    assert "Teacher (School 1)" in body  # formatted role cell
    assert "<u-badge" in body  # activated status badge
    # The searched school is preselected on the school list (deep-link friendly).
    assert 'value="school1" selected' in body


@pytest.mark.parametrize("group", ["school_class:1a", "work_group:w1a"])
def test_users_deep_link_preselects_filters(test_client: TestClient, group: str):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1", "group": group})
    assert response.status_code == 200
    body = response.text
    assert 'value="school1" selected' in body
    # The deep-linked class or work group renders preselected in the combined list.
    assert f'value="{group}" selected' in body


@pytest.mark.parametrize(
    "group",
    [
        "nonsense",
        "unknown_kind:1a",
        "school_class:",
        "",
        "all",
        "school_class:3c",  # exists, but belongs to another school
    ],
)
def test_users_deep_link_ignores_unusable_group(test_client: TestClient, group: str):
    # A stale or hand-edited link must degrade to "no group filter", not error,
    # and must not echo the unusable value back onto the control.
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1", "group": group})
    assert response.status_code == 200
    body = response.text
    # The school stays preselected; the combined list falls back to its reset option.
    assert 'value="school1" selected' in body
    assert 'value="all" selected' in body
    assert 'value="school_class:1a" selected' not in body
    assert 'value="work_group:w1a" selected' not in body
    assert "max.muster" in body  # results are unfiltered by group


def test_users_search_empty_state(test_client: TestClient):
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "NON_EXISTENT"})
    assert response.status_code == 200
    body = response.text
    assert 'slot="empty"' in body
    assert "No users found" in body


def test_login_route_redirects_to_idp(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(_StubAuth())
    response = test_client.get(
        f"{FRONTEND_PREFIX}{AUTH_LOGIN_PATH}", params={"next": "/ui/users"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "https://kc/auth?next=/ui/users"


def test_callback_route(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(_StubAuth())
    response = test_client.get(f"{FRONTEND_PREFIX}/auth/callback", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/done")


@pytest.mark.parametrize("method", ["get", "post"])
def test_logout_route(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None], method: str
):
    override_auth(_StubAuth())
    response = getattr(test_client, method)(f"{FRONTEND_PREFIX}/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "https://kc/logout"


def test_protected_route_redirects_when_unauthenticated(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(NeverAuthenticatedAdapter())
    response = test_client.get(FRONTEND_PREFIX, follow_redirects=False)
    assert response.status_code == 303
    assert AUTH_LOGIN_PATH in response.headers["location"]


def test_protected_route_htmx_redirect_when_unauthenticated(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(NeverAuthenticatedAdapter())
    response = test_client.get(FRONTEND_PREFIX, headers={"HX-Request": "true"}, follow_redirects=False)
    assert response.status_code == 200
    assert AUTH_LOGIN_PATH in response.headers["HX-Redirect"]
