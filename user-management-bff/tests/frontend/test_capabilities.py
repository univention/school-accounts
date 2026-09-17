# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""The "Capabilities and permissions" cases that today's UI can answer.

These log in as somebody other than the default account, so they only run where
the suite seeded those accounts itself -- `--kelvin_url`. Case ids refer to
`RAM-product-test-matrix.md` in `univention/dev/internal/product-tests/ucsschool`.

Most of that section is out of reach until the list view grows its selection and
the password reset dialog: CP0017-CP0029 are all phrased in terms of checkboxes
that do not exist yet.
"""

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
    sign_in_as: Callable[[str, str], Page], select_school: Callable[..., None], school: str
) -> None:
    """CP0006: a user whose only role is student reads nothing, not even themselves."""
    student = next(user for user in seed.USERS if user.roles == ["student"])

    page = sign_in_as(student.name, seed.PASSWORD)
    select_school(school, page)

    expect(page.locator("#results-region")).to_contain_text("No users found.")
