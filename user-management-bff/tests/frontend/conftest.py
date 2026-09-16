# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Fixtures for the browser-driven frontend tests.

Unlike the rest of ``tests/``, which exercises the app in process through
``TestClient``, these tests drive a real browser against a running deployment.
That is the only level at which the Keycloak login redirect chain, the design
system's custom elements and the htmx swaps they trigger are actually executed,
so this is where a regression in any of the three surfaces.

Which deployment is left entirely to ``--base-url`` and the ``--frontend_*``
credentials: the compose dev stack, the stack
``dev/scripts/start_frontend_test_stack.sh`` provisions in CI, or an installed
UCS system. Nothing here imports the application, so the suite stays usable
against a system that does not run this checkout's code.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

import pytest
from playwright.sync_api import expect

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page

# Part of the deployed URL contract rather than a setting of the run, so it is
# spelled out here instead of read from ``user_management_bff.constants``, whose
# value describes this checkout and not the system under test.
FRONTEND_PREFIX = "/univention/ucsschool/user-management/ui"


@pytest.fixture(scope="session", autouse=True)
def require_base_url(base_url: str | None) -> None:
    """Name the missing deployment instead of failing on an unresolvable relative URL."""
    if not base_url:
        pytest.fail(
            "The frontend tests drive a running deployment. Pass its address, e.g. "
            "--base-url http://user-management-proxy for the compose dev stack.",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """A UCS system serves the UI behind its own CA, and the UI follows the browser's locale."""
    return {**browser_context_args, "ignore_https_errors": True, "locale": "en-US"}


@pytest.fixture(scope="session")
def frontend_credentials(pytestconfig: pytest.Config) -> tuple[str, str]:
    return (
        cast(str, pytestconfig.getoption("frontend_username")),
        cast(str, pytestconfig.getoption("frontend_password")),
    )


@pytest.fixture
def login(page: Page, frontend_credentials: tuple[str, str]) -> Callable[..., Page]:
    """Open the UI and hand back the page with the browser past Keycloak's login form.

    Landing on the user list is asserted by URL rather than by any rendered
    string, so a login failure is reported here, by this fixture, instead of as
    a puzzling content mismatch inside the test that called it.
    """
    default_username, default_password = frontend_credentials

    def _login(username: str | None = None, password: str | None = None) -> Page:
        page.goto(f"{FRONTEND_PREFIX}/")
        page.get_by_label("Username or email").fill(username or default_username)
        page.get_by_label("Password", exact=True).fill(password or default_password)
        page.get_by_role("button", name="Sign In").click()
        expect(page).to_have_url(re.compile(rf"{re.escape(FRONTEND_PREFIX)}/users"))
        return page

    return _login


@pytest.fixture
def select_school(page: Page) -> Callable[[str], None]:
    """Pick a school in the filter sidebar and wait for the htmx swap it triggers.

    The list select has no submit button: choosing an item fires ``u-change``,
    which the form turns into a request that both replaces the results region
    and pushes the filter into the URL. Waiting for the pushed URL is therefore
    the one signal that the swap has completed, rather than merely started.
    """

    def _select(school: str) -> None:
        page.get_by_role("option", name=school, exact=True).click()
        expect(page).to_have_url(re.compile(r"[?&]school="))

    return _select
