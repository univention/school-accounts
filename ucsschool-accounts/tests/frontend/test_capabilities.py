# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

from tests.frontend import seed

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page

pytestmark = pytest.mark.usefixtures("seeded_only")


@pytest.mark.frontend
def test_only_the_schools_the_actor_is_enrolled_in_can_be_filtered_by(
    signed_in: Page, school: str
) -> None:
    """CP0001: a user can filter by every school they are enrolled in, and no other."""
    options = signed_in.locator("#school-list").get_by_role("option")

    expect(options).to_have_count(1)
    expect(options.first).to_have_text(school)


@pytest.mark.frontend
def test_a_student_sees_no_user_data(
    sign_in_as: Callable[[str, str], Page], list_school: Callable[..., None], school: str
) -> None:
    """CP0006: a user whose only role is student reads nothing, not even themselves."""
    student = next(user for user in seed.USERS if user.roles == ["student"])

    page = sign_in_as(student.name, seed.PASSWORD)
    list_school(school, page)

    expect(page.locator("#results-region")).to_contain_text("No users found.")
