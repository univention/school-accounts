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
