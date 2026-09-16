# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Fixtures for the browser-driven frontend tests.

Unlike the rest of ``tests/``, which exercises the app in process through
``TestClient``, these tests drive a real browser against a running deployment.
That is the only level at which the Keycloak login redirect chain, the design
system's custom elements and the htmx swaps they trigger are actually executed,
so this is where a regression in any of the three surfaces.

Which deployment is left entirely to ``--base-url`` and the ``--frontend_*``
options: the compose dev stack, the stack
``dev/scripts/start_frontend_test_stack.sh`` provisions in CI, or an installed
UCS system. Nothing here imports the application, so the suite stays usable
against a system that does not run this checkout's code.

The directory contents differ per deployment, so they are not assumed either.
Given ``--kelvin_url``, the suite seeds its own objects through Kelvin (see
``seed.py``) and logs in as one of them; without it, it takes the deployment's
contents as they are, from ``--frontend_school`` and ``--frontend_listed_user``,
which default to what the dev stack serves out of ``dev/data``.
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, cast

import pytest
from playwright.sync_api import expect

from tests.frontend import seed

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


@pytest.fixture(autouse=True)
def patient_expectations() -> None:
    """Playwright's 5s default is tuned for a local app, not a UCS over the network.

    Every assertion here waits on a deployment that answers from LDAP behind a
    reverse proxy, and the login redirect chain crosses Keycloak twice.
    """
    expect.set_options(timeout=15_000)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    """A UCS system serves the UI behind its own CA, and the UI follows the browser's locale."""
    return {**browser_context_args, "ignore_https_errors": True, "locale": "en-US"}


@pytest.fixture(scope="session")
def kelvin_credentials(pytestconfig: pytest.Config) -> dict[str, str] | None:
    """The system to seed through, or None to take the deployment's contents as they are."""
    host = cast("str | None", pytestconfig.getoption("kelvin_url"))
    if not host:
        return None
    return {
        "username": cast(str, pytestconfig.getoption("kelvin_username")),
        "password": cast(str, pytestconfig.getoption("kelvin_password")),
        "host": host,
    }


@pytest.fixture(scope="session", autouse=True)
def seeded(kelvin_credentials: dict[str, str] | None) -> bool:
    """Reconcile `seed`'s objects into the directory, and report whether it ran.

    Session scoped and synchronous on purpose: the tests drive Playwright's sync
    API, and seeding is a handful of calls every test in the session shares.
    There is no teardown - see `seed`'s module docstring for why removing these
    users again would break the next run's login.
    """
    if kelvin_credentials is None:
        return False
    asyncio.run(seed.provision(kelvin_credentials))
    return True


@pytest.fixture(scope="session")
def frontend_credentials(pytestconfig: pytest.Config, seeded: bool) -> tuple[str, str]:
    if seeded:
        return seed.LOGIN_USER.name, seed.PASSWORD
    return (
        cast(str, pytestconfig.getoption("frontend_username")),
        cast(str, pytestconfig.getoption("frontend_password")),
    )


@pytest.fixture(scope="session")
def school(pytestconfig: pytest.Config, seeded: bool) -> str:
    """A school the logged-in account may filter by."""
    if seeded:
        return seed.SCHOOL_DISPLAY_NAME
    return cast(str, pytestconfig.getoption("frontend_school"))


@pytest.fixture(scope="session")
def listed_user(pytestconfig: pytest.Config, seeded: bool) -> str:
    """A username the logged-in account sees once `school` is selected."""
    if seeded:
        return seed.LISTED_USER.name
    return cast(str, pytestconfig.getoption("frontend_listed_user"))


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
        # Submitting from the field rather than clicking the button: the button's
        # label comes from whichever login theme the deployment uses, the form
        # submission does not.
        page.get_by_label("Password", exact=True).press("Enter")
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
