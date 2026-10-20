# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend.conftest import FRONTEND_PREFIX

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page


@pytest.mark.frontend
def test_the_page_renders_through_the_design_system(signed_in: Page) -> None:
    expect(signed_in.locator("u-page-header")).to_have_text("School Accounts")


@pytest.mark.frontend
def test_the_user_list_starts_empty_until_a_school_is_picked(signed_in: Page) -> None:
    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a school and a group to list users."
    )


@pytest.mark.frontend
def test_selecting_a_school_asks_for_a_group(
    signed_in: Page, select_school: Callable[..., None], school: str, listed_user: str
) -> None:
    select_school(school)

    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a class or work group to list its users."
    )
    expect(signed_in.locator("#results-region")).not_to_contain_text(listed_user)


@pytest.mark.frontend
def test_all_groups_swaps_in_the_users_of_the_school(
    signed_in: Page,
    list_school: Callable[..., None],
    school: str,
    listed_user: str,
) -> None:
    list_school(school)
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)


@pytest.mark.frontend
def test_a_group_narrows_the_result_further(
    signed_in: Page, select_school: Callable[..., None], school: str
) -> None:
    """U0015: the list view can be scoped by school and by class or work group."""
    select_school(school)

    # nth(0) is "All classes and work groups".
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()

    expect(signed_in).to_have_url(re.compile(r"[?&]group="))


@pytest.mark.frontend
def test_a_filtered_list_view_is_bookmarkable(signed_in: Page, school_id: str, listed_user: str) -> None:
    """U0035: the URL carries the school and the group, and opening it reproduces the same state."""
    signed_in.goto(f"{FRONTEND_PREFIX}/users?school={school_id}&group=all")

    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)
    expect(signed_in.locator("#school-list")).to_have_attribute("value", school_id)
    expect(signed_in.locator("#group-list")).to_have_attribute("value", "all")


@pytest.mark.frontend
def test_an_unknown_school_falls_back_instead_of_failing(signed_in: Page) -> None:
    """U0036: a URL naming a school that does not exist renders the view with nothing chosen."""
    signed_in.goto(f"{FRONTEND_PREFIX}/users?school=school-that-does-not-exist")

    expect(signed_in.locator("u-table")).to_be_visible()
    expect(signed_in.locator("#results-region")).to_contain_text(
        "Select a school and a group to list users."
    )


def _choose_role(page: Page, role: str) -> None:
    page.locator(f'#role-filter u-filter-chip[value="{role}"]').click()
    expect(page).to_have_url(re.compile(rf"[?&]role={role}(&|$)"))


def _role_cells(page: Page) -> list[str]:
    return page.locator("#results-region u-tbody u-tr u-td:nth-child(5)").all_inner_texts()


@pytest.mark.frontend
def test_a_role_narrows_the_list_to_users_holding_it(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)

    _choose_role(signed_in, "teacher")

    assert all("Teacher" in cell for cell in _role_cells(signed_in))


@pytest.mark.frontend
def test_only_one_role_is_selected_at_a_time(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "student")

    _choose_role(signed_in, "teacher")

    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "teacher"
    )
    signed_in.locator('#role-filter u-filter-chip[value="teacher"]').click()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)


@pytest.mark.frontend
def test_all_clears_the_role(
    signed_in: Page, list_school: Callable[..., None], school: str, listed_user: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "student")

    signed_in.locator("#role-filter").get_by_role("button", name="All").click()

    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#results-region")).to_contain_text(listed_user)
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_count(0)


@pytest.mark.frontend
def test_a_group_change_keeps_the_role(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "teacher")

    # nth(0) is "All classes and work groups".
    signed_in.locator("#group-list").get_by_role("option").nth(1).click()

    expect(signed_in).to_have_url(re.compile(r"[?&]group=(school_class|work_group)"))
    expect(signed_in).to_have_url(re.compile(r"[?&]role=teacher(&|$)"))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "teacher"
    )


@pytest.mark.frontend
def test_the_chosen_role_keeps_the_keyboard_focus(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    signed_in.locator('#role-filter u-filter-chip[value="staff"]').focus()

    signed_in.keyboard.press("Space")

    expect(signed_in).to_have_url(re.compile(r"[?&]role=staff(&|$)"))
    expect(signed_in.locator('#role-filter u-filter-chip[value="staff"]')).to_be_focused()


@pytest.mark.frontend
def test_all_keeps_the_keyboard_focus(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    list_school(school)
    _choose_role(signed_in, "staff")
    all_button = signed_in.locator("#role-filter").get_by_role("button", name="All")
    all_button.focus()

    signed_in.keyboard.press("Space")

    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(all_button).to_be_focused()


@pytest.mark.frontend
def test_history_navigation_reruns_the_page_script_without_error(
    signed_in: Page, list_school: Callable[..., None], school: str
) -> None:
    errors: list[str] = []
    signed_in.on("pageerror", lambda error: errors.append(error.message))
    list_school(school)
    _choose_role(signed_in, "student")

    signed_in.go_back()
    expect(signed_in).not_to_have_url(re.compile(r"[?&]role="))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_count(0)
    signed_in.go_forward()
    expect(signed_in).to_have_url(re.compile(r"[?&]role=student(&|$)"))
    expect(signed_in.locator("#role-filter u-filter-chip[selected]")).to_have_attribute(
        "value", "student"
    )

    assert errors == []
