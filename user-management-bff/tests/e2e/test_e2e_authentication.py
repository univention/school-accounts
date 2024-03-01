# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_login(page: Page, base_url):
    page.goto(f"{base_url}/bff/docs")
    page.get_by_role("button", name="Authorize").click()
    with page.expect_popup() as page1_info:
        page.get_by_label("Apply given OAuth2 credentials").click()
    page1 = page1_info.value
    page1.locator("#username").fill("teacher")
    page1.locator("#password").fill("univention")
    page1.locator("#kc-login").click()
    expect(page.get_by_label("Remove authorization")).to_contain_text("Logout")
