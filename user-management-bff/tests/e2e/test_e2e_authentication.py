# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_playwright(page: Page):
    page.goto("http://user-management-proxy/univention/ucsschool/user-management/bff/docs")
    page.get_by_role("button", name="Authorize").click()
    with page.expect_popup() as page1_info:
        page.get_by_label("Apply given OAuth2 credentials").click()
    page1 = page1_info.value
    page1.get_by_label("Username or email").click()
    page1.get_by_label("Username or email").fill("dev")
    page1.get_by_label("Password", exact=True).click()
    page1.get_by_label("Password", exact=True).fill("univention")
    page1.get_by_role("button", name="Sign In").click()
    expect(page.get_by_label("Remove authorization")).to_contain_text("Logout")
