# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend import seed
from tests.frontend.conftest import tick, wait_until_held

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Locator, Page, Route


DENIED_MARK = "The selection contains users whose password you are not allowed to reset."


def row_indicator(page: Page, user_id: str) -> Locator:
    """The mark beside a row's checkbox that its password is not the actor's to reset."""
    row = page.locator("#user-rows u-tr").filter(
        has=page.locator(f'u-checkbox[name="user_id"][value="{user_id}"]')
    )
    return row.get_by_role("img", name="You are not allowed to reset this user's password.")


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
    count = signed_in.locator("#selection-form u-collapsible")
    expect(button).to_be_disabled()
    expect(count).to_be_hidden()
    # Nothing is ticked, so no user is denied and the mark stays hidden.
    expect(signed_in.get_by_role("img", name=DENIED_MARK)).to_be_hidden()

    tick(signed_in, listed_user)

    expect(count).to_be_visible()
    expect(count).to_contain_text("1 users selected")
    expect(button).to_be_enabled()


@pytest.mark.frontend
def test_an_emptied_selection_is_not_read_out_with_its_old_count(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    form = signed_in.locator("#selection-form")
    tick(signed_in, listed_user)
    expect(form.locator("u-collapsible")).to_contain_text("1 users selected")
    assert "1 users selected" in form.aria_snapshot()

    tick(signed_in, listed_user)

    expect(form.get_by_role("button", name="Reset password")).to_be_disabled()
    assert "users selected" not in form.aria_snapshot()


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


@pytest.mark.frontend
@pytest.mark.usefixtures("seeded_only")
def test_users_out_of_reach_are_flagged_before_a_reset(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """The signed-in school admin can tick themselves, for the export, but no one may
    reset a school admin's password. Their ticked row and the reset button flag it, the
    button's popup names them, and deselecting them there resets the rest.
    Seeded runs only: the File adapters grant every reset."""
    admin_name = f"{seed.LOGIN_USER.firstname} {seed.LOGIN_USER.lastname}"
    list_school(school)
    button = signed_in.locator("#password-reset")
    mark = signed_in.get_by_role("img", name=DENIED_MARK)
    popup = signed_in.locator("#password-reset-denied-dialog")
    admin_indicator = row_indicator(signed_in, seed.LOGIN_USER.name)
    # Only a ticked row shows it.
    expect(admin_indicator).to_be_hidden()
    expect(row_indicator(signed_in, listed_user)).to_have_count(0)
    tick(signed_in, listed_user)
    expect(mark).to_be_hidden()
    expect(button).not_to_have_attribute("data-tooltip", re.compile(".*"))

    tick(signed_in, seed.LOGIN_USER.name)

    expect(admin_indicator).to_be_visible()
    expect(mark).to_be_visible()
    tooltip = signed_in.locator("#tooltip")
    button.hover()
    expect(tooltip).to_be_visible()
    expect(tooltip).to_have_text(
        f"You are not allowed to reset the password of these selected users:\n{admin_name}"
    )
    admin_indicator.hover()
    expect(tooltip).to_have_text("You are not allowed to reset this user's password.")
    button.click()
    expect(popup).to_be_visible()
    named = popup.get_by_role("row")
    expect(named).to_have_count(1)
    expect(named.get_by_role("cell")).to_have_text([admin_name, seed.LOGIN_USER.name])

    popup.get_by_role("button", name="Cancel").click()

    expect(popup).to_be_hidden()
    expect(signed_in.locator("#password-reset-dialog")).to_have_count(0)
    expect(signed_in.locator("#selection-form")).to_contain_text("2 users selected")

    button.click()
    popup.get_by_role("button", name="Deselect these users").click()

    dialog = signed_in.locator("#password-reset-dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text("A new password will be set for the following 1 accounts:")
    expect(dialog.locator("u-table")).to_contain_text(listed_user)
    expect(dialog).not_to_contain_text("left out")
    expect(mark).to_be_hidden()
    expect(admin_indicator).to_be_hidden()
    expect(
        signed_in.locator(f'u-checkbox[name="user_id"][value="{seed.LOGIN_USER.name}"]')
    ).to_have_js_property("checked", False)


@pytest.mark.frontend
@pytest.mark.usefixtures("seeded_only")
def test_unticking_every_user_the_popup_names_leaves_nothing_to_reset(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    tick(signed_in, seed.LOGIN_USER.name)
    signed_in.locator("#password-reset").click()
    popup = signed_in.locator("#password-reset-denied-dialog")

    popup.get_by_role("button", name="Deselect these users").click()

    expect(popup).to_be_hidden()
    expect(signed_in.locator("#password-reset-dialog")).to_have_count(0)
    expect(signed_in.locator("#password-reset")).to_be_disabled()


@pytest.mark.frontend
def test_a_search_keeps_the_ticks_it_shows_and_drops_the_hidden_ones(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    """The rows a search brings back keep their tick. Ticks it hid are dropped, so the
    reset only ever acts on rows on screen, and clearing the search does not bring them back."""
    list_school(school)
    other = signed_in.locator(
        f'#user-rows u-checkbox[name="user_id"]:not([value="{listed_user}"])'
    ).first
    other_user = other.get_attribute("value")
    tick(signed_in, listed_user)
    other.click()
    count = signed_in.locator("#selection-form u-collapsible")
    expect(count).to_contain_text("2 users selected")

    with signed_in.expect_response(re.compile(r"/users\?(.*&)?q=")):
        signed_in.locator("#user-search input").fill(listed_user)

    listed = signed_in.locator(f'u-checkbox[name="user_id"][value="{listed_user}"]')
    expect(listed).to_have_js_property("checked", True)
    expect(count).to_contain_text("1 users selected")

    with signed_in.expect_response(re.compile(r"/users\?")):
        signed_in.locator("#user-search input").fill("")

    expect(signed_in.locator(f'u-checkbox[name="user_id"][value="{other_user}"]')).to_have_js_property(
        "checked", False
    )
    expect(listed).to_have_js_property("checked", True)
    expect(count).to_contain_text("1 users selected")


@pytest.mark.frontend
def test_typing_leaves_the_reset_button_alone(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    """The search box sits in the selection form, whose spinner is for the reset: a search
    on its way bubbles through the form's request handlers and must not start it."""
    list_school(school)
    held: list[Route] = []
    searched = re.compile(r"/users\?(.*&)?q=")
    signed_in.route(searched, lambda route: held.append(route))

    signed_in.locator("#user-search input").fill(f"nobody-{uuid.uuid4().hex[:8]}")
    wait_until_held(signed_in, held)

    reset = signed_in.locator("#selection-form u-button[type=submit]")
    assert not reset.evaluate("button => button.loading")
    held[0].continue_()
