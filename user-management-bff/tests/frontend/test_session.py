# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend.conftest import FRONTEND_PREFIX, sign_in

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page


@pytest.mark.frontend
def test_login_through_keycloak_lands_on_the_user_list(
    fresh_browser: Callable[..., Page], frontend_credentials: tuple[str, str]
) -> None:
    """G0031: logging in happens via Keycloak and lands on the list view."""
    page = fresh_browser()

    sign_in(page, *frontend_credentials)

    expect(page.locator("u-page-header")).to_have_text("User Management")


@pytest.mark.frontend
@pytest.mark.xfail(
    reason="G0039: only the path is carried through the login, the query string is dropped",
    strict=True,
)
def test_a_filtered_deep_link_survives_the_login(
    fresh_browser: Callable[..., Page], frontend_credentials: tuple[str, str], school_id: str
) -> None:
    """G0032/G0039: a deep link is reopened after the login, filters and all."""
    page = fresh_browser()

    sign_in(page, *frontend_credentials, start=f"{FRONTEND_PREFIX}/users?school={school_id}")

    expect(page).to_have_url(re.compile(rf"school={re.escape(school_id)}"))


@pytest.mark.frontend
def test_logging_out_ends_the_session(
    sign_in_as: Callable[[str, str], Page], frontend_credentials: tuple[str, str]
) -> None:
    """G0033: logout ends the session and the next request needs a new login.

    Logs in for itself: logging out the shared session would break every later test's refresh.
    """
    signed_in = sign_in_as(*frontend_credentials)
    logout = signed_in.locator("form[action$='/auth/logout'] u-button")
    expect(logout).to_be_visible()

    logout.click()
    # Not a URL: UCS redirects on into a fresh login before an assertion could see it.
    expect(signed_in.get_by_label("Username or email")).to_be_visible()

    signed_in.goto(f"{FRONTEND_PREFIX}/users")

    expect(signed_in).not_to_have_url(re.compile(rf"{re.escape(FRONTEND_PREFIX)}/users$"))
