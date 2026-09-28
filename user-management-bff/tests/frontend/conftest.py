# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Case ids refer to `RAM-product-test-matrix.md` in univention/dev/internal/product-tests/ucsschool."""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, cast

import pytest
from playwright.sync_api import expect

from tests.frontend import seed

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Browser, BrowserContext, Page, StorageState
    from pytest_playwright.pytest_playwright import CreateContextCallback

# Not from user_management_bff.constants, which describes this checkout, not the deployment.
FRONTEND_PREFIX = "/univention/ucsschool/user-management/ui"


@pytest.fixture(scope="session", autouse=True)
def require_base_url(base_url: str | None) -> None:
    if not base_url:
        pytest.fail(
            "The frontend tests drive a running deployment. Pass its address, e.g. "
            "--base-url http://user-management-proxy for the compose dev stack.",
            pytrace=False,
        )


@pytest.fixture(autouse=True)
def patient_expectations() -> None:
    expect.set_options(timeout=15_000)


@pytest.fixture(scope="session")
def kelvin_credentials(pytestconfig: pytest.Config) -> dict[str, str] | None:
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
    if seeded:
        return seed.SCHOOL_DISPLAY_NAME
    return cast(str, pytestconfig.getoption("frontend_school"))


@pytest.fixture(scope="session")
def school_id(pytestconfig: pytest.Config, seeded: bool) -> str:
    if seeded:
        return seed.SCHOOL
    return cast(str, pytestconfig.getoption("frontend_school_id"))


@pytest.fixture(scope="session")
def listed_user(pytestconfig: pytest.Config, seeded: bool) -> str:
    if seeded:
        return seed.LISTED_USER.name
    return cast(str, pytestconfig.getoption("frontend_listed_user"))


def sign_in(page: Page, username: str, password: str, start: str = f"{FRONTEND_PREFIX}/") -> None:
    page.goto(start)
    page.get_by_label("Username or email").fill(username)
    page.get_by_label("Password", exact=True).fill(password)
    # Not the button: its label depends on the deployment's login theme.
    page.get_by_label("Password", exact=True).press("Enter")
    expect(page).to_have_url(re.compile(rf"{re.escape(FRONTEND_PREFIX)}/users"))


def open_page(page: Page, path: str) -> Page:
    page.goto(path)
    expect(page).to_have_url(re.compile(re.escape(path)))
    return page


@pytest.fixture(scope="session")
def authenticated_state(
    browser: Browser, base_url: str, frontend_credentials: tuple[str, str]
) -> StorageState:
    context = browser.new_context(base_url=base_url, ignore_https_errors=True, locale="en-US")
    try:
        sign_in(context.new_page(), *frontend_credentials)
        return context.storage_state()
    finally:
        context.close()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    # No locale or cookies here: a test could not override them in new_context.
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture
def context(new_context: CreateContextCallback, authenticated_state: StorageState) -> BrowserContext:
    return new_context(locale="en-US", storage_state=authenticated_state)


@pytest.fixture
def signed_in(page: Page) -> Page:
    return open_page(page, f"{FRONTEND_PREFIX}/users")


@pytest.fixture
def fresh_browser(new_context: CreateContextCallback) -> Callable[[], Page]:
    def _open() -> Page:
        return new_context(locale="en-US").new_page()

    return _open


@pytest.fixture
def open_in_language(
    new_context: CreateContextCallback, authenticated_state: StorageState
) -> Callable[[str], Page]:
    def _open(language: str) -> Page:
        page = new_context(locale=language, storage_state=authenticated_state).new_page()
        return open_page(page, f"{FRONTEND_PREFIX}/users")

    return _open


@pytest.fixture
def sign_in_as(fresh_browser: Callable[[], Page]) -> Callable[[str, str], Page]:
    def _sign_in_as(username: str, password: str) -> Page:
        page = fresh_browser()
        sign_in(page, username, password)
        return page

    return _sign_in_as


@pytest.fixture
def seeded_only(seeded: bool) -> None:
    if not seeded:
        pytest.skip("needs --kelvin_url: the roles under test are seeded through Kelvin")


@pytest.fixture
def select_school(request: pytest.FixtureRequest) -> Callable[..., None]:
    def _select(school: str, page: Page | None = None) -> None:
        page = page or cast("Page", request.getfixturevalue("signed_in"))
        # The group control is swapped separately from the results, and until then
        # it still offers the previous school's options.
        with page.expect_response(re.compile(r"/users/filters\?")):
            page.get_by_role("option", name=school, exact=True).click()
        # The pushed URL is the one sign that the htmx swap finished, not just started.
        expect(page).to_have_url(re.compile(r"[?&]school="))

    return _select


@pytest.fixture
def list_school(
    request: pytest.FixtureRequest, select_school: Callable[..., None]
) -> Callable[..., None]:
    def _list(school: str, page: Page | None = None) -> None:
        page = page or cast("Page", request.getfixturevalue("signed_in"))
        select_school(school, page=page)
        # By value, not label: the label follows the browser language.
        page.locator('#group-list u-list-select-item[value="all"]').click()
        expect(page).to_have_url(re.compile(r"[?&]group=all(&|$)"))

    return _list
