# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend import seed

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Locator, Page


def tick(page: Page, username: str) -> None:
    page.locator(f'u-checkbox[name="user_id"][value="{username}"]').click()


def open_reset_dialog(page: Page, button: str = "Reset password") -> Locator:
    page.locator("#selection-form").get_by_role("button", name=button).click()
    dialog = page.locator("#password-reset-dialog")
    expect(dialog).to_be_visible()
    return dialog


@pytest.mark.frontend
def test_ticking_a_user_counts_the_selection_and_enables_the_reset(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    button = signed_in.locator("#selection-form").get_by_role("button", name="Reset password")
    # Visibility, not text: x-show hides the span but keeps its text in the DOM.
    expect(signed_in.locator("#selection-form").get_by_text("No users selected")).to_be_visible()
    expect(button).to_be_disabled()

    tick(signed_in, listed_user)

    expect(signed_in.locator("#selection-form").get_by_text("1 users selected")).to_be_visible()
    expect(signed_in.locator("#selection-form").get_by_text("No users selected")).to_be_hidden()
    expect(button).to_be_enabled()


@pytest.mark.frontend
def test_the_dialog_lists_the_selection_and_cancel_changes_nothing(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    tick(signed_in, listed_user)

    dialog = open_reset_dialog(signed_in)

    expect(dialog).to_contain_text("A new password will be set for the following 1 accounts:")
    expect(dialog.locator("u-table")).to_contain_text(listed_user)
    expect(dialog.get_by_role("button", name="Set password")).to_be_disabled()

    dialog.get_by_role("button", name="Cancel").click()

    expect(dialog).to_be_hidden()
    expect(signed_in.locator("#password-reset-result")).to_be_empty()
    expect(signed_in.locator("#selection-form")).to_contain_text("1 users selected")


@pytest.mark.frontend
def test_the_selection_count_and_the_dialog_are_localized(
    open_in_language: Callable[[str], Page],
    list_school: Callable[..., None],
    school: str,
    listed_user: str,
) -> None:
    """L0005/L0012: the live selection count and the confirmation dialog follow the browser language."""
    page = open_in_language("de-DE")
    list_school(school, page=page)
    tick(page, listed_user)

    expect(page.locator("#selection-form").get_by_text("1 Benutzer ausgewählt")).to_be_visible()

    dialog = open_reset_dialog(page, button="Passwort zurücksetzen")

    expect(dialog).to_contain_text("Für die folgenden 1 Konten wird ein neues Passwort gesetzt:")
    expect(dialog.get_by_role("button", name="Passwort setzen")).to_be_disabled()


@pytest.mark.frontend
@pytest.mark.usefixtures("seeded_only")
def test_a_reset_password_is_the_one_the_account_logs_in_with(
    signed_in: Page,
    list_school: Callable[..., None],
    sign_in_as: Callable[[str, str], Page],
    school: str,
) -> None:
    """U0029: a school admin resets a teacher, who then logs in with the new password.

    Seeded runs only: on the File adapters the reset rewrites `dev/data/users.json`.
    """
    target = next(user for user in seed.USERS if user.name == "maria.kaiser")
    password = f"umtest.{uuid.uuid4().hex[:12]}.Reset"
    list_school(school)
    tick(signed_in, target.name)
    dialog = open_reset_dialog(signed_in)

    dialog.locator('u-input[name="password"] input').fill(password)
    dialog.locator("u-confirm-action").get_by_role("checkbox").check()
    dialog.get_by_role("button", name="Set password").click()

    expect(dialog).to_be_hidden()
    expect(signed_in.locator("#toast-region")).to_contain_text("Password reset for 1 of 1 users.")
    expect(signed_in.locator("#password-reset-result")).not_to_contain_text(target.name)
    sign_in_as(target.name, password)
