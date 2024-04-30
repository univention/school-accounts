# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only


import os
from playwright.sync_api import Page, expect


def test_has_title(page: Page):
    page.goto("/univention/ucsschool/user-management/ui/")

    if os.getenv("CI_INTEGRATION"):
        page.get_by_label("Username or email").fill("alex.admin")
        page.get_by_label("Password", exact=True).fill("univention")
        page.get_by_label("Password", exact=True).press("Enter")
    expect(page.get_by_role("heading", name="Users (schools)")).to_be_visible()
