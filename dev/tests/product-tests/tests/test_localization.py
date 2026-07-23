# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from playwright.sync_api import expect, Page


def test_localization_settings(page_login, admin_login):
    """
    Tests: L0001, L0002
    """
    page: Page = page_login(**admin_login)
    expect(page.get_by_label("Language")).to_contain_text("DeutschEnglish")
    expect(page.get_by_label("Language")).to_have_value("en-US")
    expect(page.locator("h2")).to_contain_text("Management of school users")
    page.get_by_label("Language").select_option("de-DE")
    expect(page.get_by_label("Sprache")).to_have_value("de-DE")
    expect(page.locator("h2")).to_contain_text("Verwaltung von Schulbenutzern")
