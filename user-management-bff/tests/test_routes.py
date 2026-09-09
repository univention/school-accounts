# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Tests for the UI router (shell + interactive-login routes)."""

import re
import sys
from typing import Any, Callable, Coroutine, Generator, cast
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import Scope

from user_management_bff.adapters.authentication import NeverAuthenticatedAdapter
from user_management_bff.adapters.permissions import FilePermissionsAdapter
from user_management_bff.adapters.school_classes import FileSchoolClassesPersistenceAdapter
from user_management_bff.adapters.schools import FileSchoolsPersistenceAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.adapters.work_groups import FileWorkGroupsPersistenceAdapter
from user_management_bff.constants import AUTH_LOGIN_PATH, FRONTEND_PREFIX
from user_management_bff.errors import (
    KelvinAPIUnavailableError,
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
from user_management_bff.main import (
    CORRELATION_ID_HEADER_NAME,
    CORRELATION_ID_MAX_LENGTH,
    app,
)
from user_management_bff.models import Permission
from user_management_bff.ports import FastAPIAuthenticationPort
from user_management_bff.routes import auth_port, render_static

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


class _NamedAuth(_StubAuth):
    @override
    async def get_display_name(self, request: Request) -> str:
        return "Mina Teacher"


class _CsrfIssuingAuth(FastAPIAuthenticationPort):
    """Auth adapter double issuing a known, recognisable CSRF token."""

    TOKEN: str = "token-from-the-session"

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep(request: Request) -> str:
            return await self.get_authenticated_id(request)

        return _dep

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        return "dev"

    @override
    async def issue_csrf_token(self, request: Request) -> str:
        return self.TOKEN


class _CsrfRejectAuth(FastAPIAuthenticationPort):
    """Auth adapter double whose CSRF check always rejects."""

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep(request: Request) -> str:
            return await self.get_authenticated_id(request)

        return _dep

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        return "dev"

    @override
    async def check_csrf(self, request: Request, submitted: str | None) -> bool:
        return False


@pytest.fixture
def override_auth() -> Generator[Callable[[FastAPIAuthenticationPort], None], None, None]:
    def _override(adapter: FastAPIAuthenticationPort) -> None:
        app.dependency_overrides[auth_port] = lambda: adapter

    yield _override
    app.dependency_overrides.pop(auth_port, None)


def _lower_the_reset_limit(mocker: MockerFixture, limit: int) -> None:
    """Lower the ceiling on how many accounts one reset may name.

    A route crosses both modules and each reads the constant at call time, so
    patching only one leaves the other enforcing the real limit.
    """
    mocker.patch("user_management_bff.business_logic.PASSWORD_RESET_MAX_TARGETS", limit)
    mocker.patch("user_management_bff.presentation.PASSWORD_RESET_MAX_TARGETS", limit)


def _post_reset(
    test_client: TestClient,
    user_id: str | list[str],
    password: str | None = "new-password",
    **extra: str,
) -> httpx.Response:
    """Submit the reset form. ``password=None`` omits the field entirely, which is a
    different request from submitting it empty."""
    data: dict[str, str | list[str]] = {"user_id": user_id, **extra}
    if password is not None:
        data["password"] = password
    # TestClient is typed against the absent httpx2, so its calls come back Unknown.
    return cast(
        httpx.Response,
        test_client.post(  # pyright: ignore[reportUnknownMemberType]
            f"{FRONTEND_PREFIX}/users/password-reset", data=data
        ),
    )


def _post_confirm(test_client: TestClient, user_id: str | list[str]) -> httpx.Response:
    """Ask for the confirmation dialog over a selection."""
    # TestClient is typed against the absent httpx2, so its calls come back Unknown.
    return cast(
        httpx.Response,
        test_client.post(  # pyright: ignore[reportUnknownMemberType]
            f"{FRONTEND_PREFIX}/users/password-reset/confirm", data={"user_id": user_id}
        ),
    )


def test_root_redirects_to_users(test_client: TestClient):
    response = test_client.get(FRONTEND_PREFIX, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/users")


def test_an_oversized_request_id_is_capped(test_client: TestClient):
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users", headers={CORRELATION_ID_HEADER_NAME: "x" * 5000}
    )
    assert response.headers[CORRELATION_ID_HEADER_NAME] == "x" * CORRELATION_ID_MAX_LENGTH


@pytest.mark.parametrize(
    ("headers", "status_code", "retarget"),
    [({}, 500, None), ({"HX-Request": "true"}, 200, "#toast-region")],
    ids=["page", "htmx"],
)
def test_an_unhandled_error_still_carries_the_request_id(
    test_client: TestClient,
    mocker: MockerFixture,
    headers: dict[str, str],
    status_code: int,
    retarget: str | None,
):
    mocker.patch.object(FileUsersPersistenceAdapter, "get_users", side_effect=RuntimeError("boom"))
    # The session client's lifespan already configured the adapters; this one only stops re-raising.
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(
        f"{FRONTEND_PREFIX}/users",
        params={"school": "school1"},
        headers={**headers, CORRELATION_ID_HEADER_NAME: "abc"},
    )
    assert response.status_code == status_code
    assert response.headers.get("HX-Retarget") == retarget
    assert response.headers[CORRELATION_ID_HEADER_NAME] == "abc"
    assert "An unexpected error occurred" in response.text


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
    assert 'hx-trigger="u-change[filterChanged(event)] from:#school-list"' in body
    # Sidebar next to the results column, both stretched to full height.
    assert 'align="stretch"' in body and 'basis="sm"' in body
    # Changing either list searches immediately; there is no submit button. Both
    # triggers are guarded: the list select fires u-change on a click that re-picks
    # the active item too, and refetching would discard the selection.
    assert 'hx-trigger="u-change[filterChanged(event)] delay:100ms"' in body
    assert 'type="submit"' not in body[body.index("<u-form") : body.index("</u-form>")]
    # The combined list carries an explicit reset option, preselected while no
    # class or work group is chosen.
    assert 'value="all" selected' in body
    assert "All classes and work groups" in body
    # Only the route's HX-Push-Url pushes: the attribute would also push after an
    # error toast, recording a filter whose results never loaded.
    assert "hx-push-url" not in body
    assert 'hx-select="#results-region"' in body
    # The cascade (school -> filters) must not inherit the form's select,
    # or its fragment response would blank out the dependent filters.
    assert 'hx-disinherit="hx-select"' in body
    # htmx snapshots the page after the click that set the school but before the
    # results swap, so a restored snapshot pairs a school with the old table.
    assert 'hx-history="false"' in body
    assert response.headers["HX-Push-Url"] == f"{FRONTEND_PREFIX}/users"
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


def _users_page(test_client: TestClient, accept_language: str, **params: str) -> str:
    # Starlette annotates TestClient against httpx2, which this project does not
    # install, so every httpx type in its signature resolves to Unknown. The cast
    # confines that to one call site instead of leaking into every assertion.
    # TestClient is typed against the absent httpx2, so its calls come back Unknown.
    response = cast(
        httpx.Response,
        test_client.get(  # pyright: ignore[reportUnknownMemberType]
            f"{FRONTEND_PREFIX}/users",
            params=params,
            headers={"Accept-Language": accept_language},
        ),
    )
    assert response.status_code == 200
    return response.text


def test_german_accept_language_renders_german_template_strings(test_client: TestClient):
    """Every string asserted here lives in a Jinja template, not in Python."""
    body = _users_page(test_client, "de-DE,de;q=0.9")
    assert '<html lang="de"' in body
    assert "<title>UCS@school Benutzerverwaltung</title>" in body  # base.html
    assert "Benutzerverwaltung</u-page-header>" in body  # macros/layout.html
    assert "Zum dunklen Design wechseln" in body  # macros/layout.html
    assert "Klassen &amp; Arbeitsgruppen" in body  # fragments/user_filters.html, escaped "&"
    assert "Alle Klassen und Arbeitsgruppen" in body  # fragments/group_options.html
    assert "Schulen filtern" in body  # pages/user_list.html


def test_german_accept_language_translates_runtime_composed_role_msgids(test_client: TestClient):
    """The role label reaches `_()` through a variable, so only `N_` markers extract it."""
    body = _users_page(test_client, "de", school="school1")
    assert "Lehrer (School 1)" in body
    assert "Teacher (School 1)" not in body


def test_german_accept_language_renders_the_password_reset_dialog_in_german(
    test_client: TestClient,
):
    """The dialog is rendered from its own fragment, so the page-level test above
    never reaches it - and an unextracted string there fails silently in English."""
    response = test_client.post(
        f"{FRONTEND_PREFIX}/users/password-reset/confirm",
        data={"user_id": "test_user1"},
        headers={"Accept-Language": "de"},
    )
    assert response.status_code == 200
    body = response.text
    assert "Passwort zurücksetzen" in body  # heading
    assert "Neues Passwort" in body  # the password field's label
    assert "Passwort setzen" in body  # the submit
    assert "Abbrechen" in body
    assert "Setzt die Passwörter zurück für" in body  # the confirmation gate
    assert "Set password" not in body


def test_english_accept_language_still_renders_english(test_client: TestClient):
    body = _users_page(test_client, "en-GB,en")
    assert '<html lang="en"' in body
    assert "<title>UCS@school User Management</title>" in body
    assert "Benutzerverwaltung" not in body


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


def test_logout_route(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(_StubAuth())
    response = test_client.post(f"{FRONTEND_PREFIX}/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "https://kc/logout"


def test_logout_route_rejects_get(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(_StubAuth())
    response = test_client.get(f"{FRONTEND_PREFIX}/auth/logout", follow_redirects=False)
    assert response.status_code == 405


def test_header_logs_out_under_the_display_name(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    override_auth(_NamedAuth())
    body = test_client.get(f"{FRONTEND_PREFIX}/users").text
    assert f'<form method="post" action="{FRONTEND_PREFIX}/auth/logout">' in body
    assert "Mina Teacher (logout)" in body


def test_header_falls_back_to_the_actor_id(test_client: TestClient):
    assert "dev (logout)" in test_client.get(f"{FRONTEND_PREFIX}/users").text


def test_a_page_rendered_without_an_actor_has_no_logout_button():
    scope: Scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""}
    body = bytes(render_static(Request(scope), "pages/message.html", message="Nope").body)
    assert b"auth/logout" not in body


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


def test_error_toast_is_not_swapped_out_of_band(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    """The global handler retargets the whole fragment, so an oob swap would double it."""
    override_auth(_CsrfRejectAuth())
    response = test_client.post(
        f"{FRONTEND_PREFIX}/users/password-reset",
        data={"user_id": "test_user1", "password": "new-password"},
        headers={"HX-Request": "true"},
    )
    assert response.headers["HX-Retarget"] == "#toast-region"
    assert "hx-swap-oob" not in response.text


@pytest.mark.parametrize(
    "path,data",
    [
        ("/users/password-reset", {"user_id": "test_user1", "password": "new-password"}),
        ("/users/password-reset/confirm", {"user_id": "test_user1"}),
    ],
)
def test_unsafe_routes_reject_a_missing_csrf_token(
    test_client: TestClient,
    override_auth: Callable[[FastAPIAuthenticationPort], None],
    path: str,
    data: dict[str, str],
):
    """Every unsafe method carries the token, including the one that only renders."""
    override_auth(_CsrfRejectAuth())
    response = test_client.post(f"{FRONTEND_PREFIX}{path}", data=data)
    assert response.status_code == 403
    assert "security token" in response.text


def test_password_reset_happy_path(
    test_client: TestClient, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    patch_set_password({})
    response = _post_reset(test_client, ["test_user1", "test_user2"], "new-password")
    assert response.status_code == 200
    assert "2 of 2" in response.text
    assert 'variant="success"' in response.text
    # All-succeeded is the toast's job; nothing is listed per user.
    assert 'data-target-id="' not in response.text
    # htmx inserts an OOB element's *children*, so the wrapper carries the attribute.
    assert re.search(r'<div hx-swap-oob="beforeend:#toast-region">\s*<u-toast-item', response.text)


def test_password_reset_never_echoes_the_password(
    test_client: TestClient, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """The one value in this flow that must not survive into a response."""
    secret = "n0t-in-the-response"  # noqa: S105
    patch_set_password({})
    response = _post_reset(test_client, ["test_user1", "test_user2"], secret)
    assert response.status_code == 200
    assert secret not in response.text
    assert secret not in str(response.headers)


def test_password_reset_never_echoes_a_rejected_password(
    test_client: TestClient, rejecting_set_password: Callable[[str | Callable[[str], str]], MagicMock]
):
    """Not even on the failure path, where the backend's reason is rendered."""
    secret = "n0t-in-the-response"  # noqa: S105
    rejecting_set_password("policy violation")
    response = _post_reset(test_client, "test_user1", secret)
    assert "policy violation" in response.text
    assert secret not in response.text


def test_password_reset_permission_denied(test_client: TestClient, mocker: MockerFixture):
    mocker.patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
    response = _post_reset(test_client, "test_user1", "new-password")
    assert response.status_code == 200
    assert "0 of 1" in response.text
    assert 'variant="error"' in response.text


def test_a_partial_failure_lists_only_the_accounts_that_failed(
    test_client: TestClient, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """Two things about one response: it counts, and it keeps only the failures
    ticked so a retry does not mean hunting them down in the table again."""
    patch_set_password({"test_user2": ObjectNotFoundError(identifier="test_user2")})
    response = _post_reset(test_client, ["test_user1", "test_user2"], "new-password")
    assert response.status_code == 200
    assert "1 of 2" in response.text
    assert 'variant="error"' in response.text
    assert 'data-target-id="test_user2"' in response.text
    assert 'data-target-id="test_user1"' not in response.text


def test_a_refused_password_reopens_the_dialog_over_the_selection_the_write_resolved(
    test_client: TestClient,
    mocker: MockerFixture,
    rejecting_set_password: Callable[[str | Callable[[str], str]], MagicMock],
):
    """Nothing was written and every attempt failed alike, so the password is at fault
    and its reason belongs on the field. Re-rendering the dialog must then cost nothing:
    the write already read every target and asked Cerbos about all of them."""
    rejecting_set_password("Password too short")
    permissions_spy = mocker.spy(FilePermissionsAdapter, "get_permissions")
    response = _post_reset(test_client, ["test_user1", "test_user2"], "short")
    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#password-reset-dialog-region"
    assert 'error="Password too short"' in response.text
    assert "<dialog" in response.text
    assert 'value="test_user1"' in response.text and 'value="test_user2"' in response.text
    assert permissions_spy.call_count == 1


def test_password_reset_differing_reasons_stay_in_the_result_list(
    test_client: TestClient, rejecting_set_password: Callable[[str | Callable[[str], str]], MagicMock]
):
    """Reasons that differ per user are about the users, not the password."""
    rejecting_set_password(lambda identifier: f"rejected {identifier}")
    response = _post_reset(test_client, ["test_user1", "test_user2"], "new-password")
    assert "HX-Retarget" not in response.headers
    assert "Rejected" in response.text
    assert "rejected test_user1" in response.text and "rejected test_user2" in response.text


def test_password_reset_a_partial_success_stays_in_the_result_list(
    test_client: TestClient, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """One success means the password worked, so the failure is that user's."""
    patch_set_password(
        {"test_user2": PasswordResetRejectedError(identifier="test_user2", message="Password too short")}
    )
    response = _post_reset(test_client, ["test_user1", "test_user2"], "new-password")
    assert "HX-Retarget" not in response.headers
    assert "1 of 2" in response.text
    assert "Password too short" in response.text


def test_password_reset_reports_an_account_that_cannot_be_forced_to_change_it(
    test_client: TestClient, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """The password is left alone, so the account belongs in the failure list."""
    patch_set_password(
        {"test_user2": PasswordChangeOnNextLoginUnsupportedError(identifier="test_user2")}
    )
    response = _post_reset(test_client, ["test_user1", "test_user2"], change_on_next_login="on")
    assert "HX-Retarget" not in response.headers
    assert "1 of 2" in response.text
    assert 'variant="error"' in response.text
    assert 'data-target-id="test_user2"' in response.text
    assert "the password was left unchanged" in response.text


def test_password_reset_confirm_refuses_an_oversized_selection_as_a_toast(
    test_client: TestClient, mocker: MockerFixture
):
    """No dialog: nothing was resolved, so it would have nothing to state. The
    wording is the submit's, and no user is fetched to produce it."""
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    _lower_the_reset_limit(mocker, 2)
    response = _post_confirm(test_client, ["test_user1", "test_user2", "test_user3"])
    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#toast-region"
    assert response.headers["HX-Reswap"] == "beforeend"
    assert "Select at most 2 users at once" in response.text
    assert 'variant="error"' in response.text
    assert "<dialog" not in response.text
    get_user_mock.assert_not_called()


def test_password_reset_unknown_user_reports_not_found(test_client: TestClient):
    response = _post_reset(test_client, "NON_EXISTENT", "new-password")
    assert response.status_code == 200
    assert "0 of 1" in response.text
    assert 'variant="error"' in response.text


def test_password_reset_no_users_selected_shows_error(test_client: TestClient):
    response = test_client.post(
        f"{FRONTEND_PREFIX}/users/password-reset",
        data={"password": "new-password"},  # no user_id at all, so not _post_reset
    )
    assert response.status_code == 200
    assert 'variant="error"' in response.text
    assert "Password reset for" not in response.text
    assert "Select at least one user" in response.text


def test_password_reset_too_many_targets_is_refused(test_client: TestClient, mocker: MockerFixture):
    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", new_callable=mocker.AsyncMock
    )
    _lower_the_reset_limit(mocker, 2)
    response = _post_reset(test_client, ["test_user1", "test_user2", "test_user3"])
    assert response.status_code == 200
    assert 'variant="error"' in response.text
    assert "Select at most 2 users at once" in response.text
    set_password_mock.assert_not_called()


@pytest.mark.parametrize(
    "password",
    [pytest.param("", id="submitted-empty"), pytest.param(None, id="field-absent")],
)
def test_password_reset_without_a_password_is_refused(
    test_client: TestClient,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
    password: str | None,
):
    """A browser that drops the field and one that sends it blank must read alike."""
    set_password_mock = patch_set_password({})
    response = _post_reset(test_client, "test_user1", password)
    assert response.status_code == 200
    assert 'variant="error"' in response.text
    assert "A new password is required" in response.text
    set_password_mock.assert_not_called()


def test_changing_a_filter_starts_a_fresh_selection(test_client: TestClient):
    """A new filter is a new selection: the filter form does not send the ticked ids,
    and a request naming them anyway gets a list with nothing selected."""
    body = test_client.get(
        f"{FRONTEND_PREFIX}/users", params={"school": "school1", "user_id": ["user1", "elsewhere"]}
    ).text
    filter_form, selection_form = body.split('id="selection-form"', 1)
    assert "hx-include" not in filter_form
    rows = selection_form[selection_form.index("<u-tbody>") : selection_form.index("</u-tbody>")]
    assert "checked" not in rows
    assert '<input type="hidden" name="user_id"' not in selection_form


def test_the_selection_form_carries_its_school_to_the_confirm_post(test_client: TestClient):
    """The confirm route resolves the selection within the school it was made in."""
    body = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"}).text
    selection_form = body[body.index('id="selection-form"') :]
    assert '"school": "school1"' in selection_form


def test_only_the_posting_form_sends_the_csrf_token(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    """The filter form only ever GETs, and htmx inherits hx-headers, so declaring the
    token any higher would attach it to every safe request on the page."""
    override_auth(_CsrfIssuingAuth())
    body = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"}).text
    filter_form, selection_form = body.split('id="selection-form"', 1)
    assert f'{{"X-CSRF-Token": "{_CsrfIssuingAuth.TOKEN}"}}' in selection_form
    assert "hx-headers" not in filter_form


def test_users_list_pushed_url_keeps_the_group_filter(test_client: TestClient):
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users", params={"school": "school1", "group": "school_class:1a"}
    )
    assert response.headers["HX-Push-Url"] == (
        f"{FRONTEND_PREFIX}/users?school=school1&group=school_class%3A1a"
    )


def test_users_list_reads_each_school_once_per_request(test_client: TestClient, mocker: MockerFixture):
    """The filter sidebar and the table overlap; the request-scoped cache in the DI
    layer is what stops the overlap being fetched twice.

    The sidebar has to load the selected school in full, so the table's groups for
    that school come out of the cache - what reaches the backend a second time is
    only the other schools, and only the names actually rendered.
    """
    schools_spy = mocker.spy(FileSchoolsPersistenceAdapter, "get_schools")
    all_classes_spy = mocker.spy(FileSchoolClassesPersistenceAdapter, "get_school_classes")
    all_work_groups_spy = mocker.spy(FileWorkGroupsPersistenceAdapter, "get_work_groups")
    classes_spy = mocker.spy(FileSchoolClassesPersistenceAdapter, "get_school_classes_by_name")
    work_groups_spy = mocker.spy(FileWorkGroupsPersistenceAdapter, "get_work_groups_by_name")

    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school2"})
    assert response.status_code == 200

    # The school list is needed for the filter and to name each user's schools.
    assert schools_spy.call_count == 1
    # Once each for the sidebar, and only for the selected school.
    # ``args[0]`` is the adapter instance - these spy on the class.
    assert [call.args[1] for call in all_classes_spy.call_args_list] == ["school2"]
    assert [call.args[1] for call in all_work_groups_spy.call_args_list] == ["school2"]
    # school1 comes from user3, who is listed under school2 but holds classes in
    # school1. school2's own groups are already cached from the sidebar, so the
    # table's lookup for it never reaches the adapter.
    assert [call.args[1:] for call in classes_spy.call_args_list] == [("school1", ["1a", "2b"])]
    assert [call.args[1:] for call in work_groups_spy.call_args_list] == [("school1", ["w2b"])]


def test_password_reset_confirm_renders_the_dialog(test_client: TestClient):
    response = _post_confirm(test_client, ["test_user1", "test_user2"])
    assert response.status_code == 200
    body = response.text
    assert re.search(r'<dialog\s+id="password-reset-dialog"', body)
    assert "following 2 accounts" in body
    assert '<input type="hidden" name="user_id" value="test_user1" />' in body
    assert '<input type="hidden" name="user_id" value="test_user2" />' in body
    # new-password so the browser cannot offer the actor's own credentials.
    assert 'autocomplete="new-password"' in body


def test_render_puts_the_sessions_csrf_token_in_the_dialog(
    test_client: TestClient, override_auth: Callable[[FastAPIAuthenticationPort], None]
):
    """The token comes from render(), so a form only has to name {{ csrf_token }}."""
    override_auth(_CsrfIssuingAuth())
    response = _post_confirm(test_client, "test_user1")
    assert f'{{"X-CSRF-Token": "{_CsrfIssuingAuth.TOKEN}"}}' in response.text


def test_password_reset_confirm_does_not_promise_a_list_it_will_not_render(
    test_client: TestClient, mocker: MockerFixture
):
    """Above PASSWORD_RESET_NAMED_LIMIT no names are rendered, so the sentence must
    not end on a colon - between that limit and the bulk threshold nothing follows it."""
    mocker.patch("user_management_bff.presentation.PASSWORD_RESET_NAMED_LIMIT", 1)
    response = _post_confirm(test_client, ["test_user1", "test_user2"])
    body = response.text
    assert "will be set for 2 accounts." in body
    assert "the following" not in body


def test_password_reset_confirm_warns_about_a_role_spanning_selection(test_client: TestClient):
    """test_user1 is a teacher, test_user4 a school admin - disjoint roles."""
    response = _post_confirm(test_client, ["test_user1", "test_user4"])
    body = response.text
    assert "Several roles in one selection" in body


@pytest.mark.parametrize("supported", [True, False])
def test_password_reset_confirm_offers_change_on_next_login_only_when_supported(
    test_client: TestClient, mocker: MockerFixture, supported: bool
):
    """Kelvin 422s an unmapped udm_property, which would fail the reset itself."""
    mocker.patch.object(
        FileUsersPersistenceAdapter,
        "supports_password_change_on_next_login",
        return_value=supported,
    )
    response = _post_confirm(test_client, ["test_user1"])
    assert ('name="change_on_next_login"' in response.text) is supported


def test_password_reset_forwards_change_on_next_login(test_client: TestClient, mocker: MockerFixture):
    set_password = mocker.patch.object(FileUsersPersistenceAdapter, "set_password")
    _post_reset(test_client, ["test_user1"], change_on_next_login="on")
    set_password.assert_awaited_once_with("test_user1", "new-password", True)


def test_password_reset_without_the_box_ticked_does_not_force_a_change(
    test_client: TestClient, mocker: MockerFixture
):
    set_password = mocker.patch.object(FileUsersPersistenceAdapter, "set_password")
    _post_reset(test_client, ["test_user1"], "new-password")
    set_password.assert_awaited_once_with("test_user1", "new-password", False)


def test_password_reset_confirm_reports_accounts_it_may_not_reset(
    test_client: TestClient, mocker: MockerFixture
):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        return_value={"test_user1": [Permission.write_password]},
    )
    response = _post_confirm(test_client, ["test_user1", "test_user2"])
    assert "not yours to reset" in response.text


def test_password_reset_confirm_with_nothing_resettable_offers_only_a_close(
    test_client: TestClient, mocker: MockerFixture
):
    mocker.patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
    response = _post_confirm(test_client, "test_user1")
    body = response.text
    assert "None of the selected accounts" in body
    assert 'name="password"' not in body


def test_a_kelvin_failure_becomes_a_toast_for_htmx(test_client: TestClient, mocker: MockerFixture):
    """htmx swaps nothing on a 5xx, so an unhandled backend failure shows the user nothing."""
    mocker.patch.object(
        FileUsersPersistenceAdapter, "get_users", side_effect=KelvinAPIUnavailableError()
    )
    response = test_client.get(
        f"{FRONTEND_PREFIX}/users", params={"school": "school1"}, headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#toast-region"
    # Without this the filter form's hx-select="#results-region" picks nothing out of the
    # toast fragment and htmx swaps an empty string over the toast region.
    assert response.headers["HX-Reselect"] == "unset"
    assert "currently unavailable" in response.text


def test_a_kelvin_failure_becomes_a_message_page_without_htmx(
    test_client: TestClient, mocker: MockerFixture
):
    mocker.patch.object(
        FileUsersPersistenceAdapter, "get_users", side_effect=KelvinAPIUnavailableError()
    )
    response = test_client.get(f"{FRONTEND_PREFIX}/users", params={"school": "school1"})
    assert response.status_code == 502
    assert "currently unavailable" in response.text
