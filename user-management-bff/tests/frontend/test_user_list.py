# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Smoke coverage for the user list, and the worked examples for the harness.

Deliberately thin: these assert the three things the harness itself has to get
right -- the login redirect chain completes, a page renders through the design
system's custom elements, and an htmx swap replaces the results region -- so a
broken harness fails here rather than inside a product test written on top of
it. Product test cases belong in their own modules next to this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page


@pytest.mark.frontend
def test_login_lands_on_the_user_list(login: Callable[..., Page]) -> None:
    page = login()
    expect(page.locator("u-page-header")).to_have_text("User Management")


@pytest.mark.frontend
def test_the_user_list_starts_empty_until_a_school_is_picked(login: Callable[..., Page]) -> None:
    page = login()
    expect(page.locator("#results-region")).to_contain_text("No users found.")


@pytest.mark.frontend
def test_selecting_a_school_swaps_in_its_users(
    login: Callable[..., Page],
    select_school: Callable[[str], None],
    school: str,
    listed_user: str,
) -> None:
    page = login()
    select_school(school)
    expect(page.locator("#results-region")).to_contain_text(listed_user)
