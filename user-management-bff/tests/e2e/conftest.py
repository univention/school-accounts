# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Callable

import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return pytestconfig.getoption("base_url")


@pytest.fixture(scope="session", autouse=True)
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture
def access_token(page: Page, base_url) -> Callable[[str, str], str]:
    def wrapper(username: str, password: str) -> str:
        page.goto(f"{base_url}/bff/docs")
        page.get_by_role("button", name="Authorize").click()
        with page.expect_popup() as page1_info:
            page.get_by_label("Apply given OAuth2 credentials").click()
        page1 = page1_info.value
        page1.locator("#username").fill(username)
        page1.locator("#password").fill(password)
        page1.locator("#kc-login").click()
        with page.expect_response(
            "https://ucs-sso-ng.school.test/realms/ucs/protocol/openid-connect/token"
        ) as response_info:
            response = response_info.value
            assert response.status == 200
            data = response.json()
            return data["access_token"]

    return wrapper
