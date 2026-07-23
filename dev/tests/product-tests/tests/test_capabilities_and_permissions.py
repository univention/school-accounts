# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os

import pytest
import secrets
from playwright.sync_api import expect, Page

from ucsschool.kelvin.client import User

pytestmark = pytest.mark.skipif(
    os.getenv("CI_INTEGRATION") is None, reason="Only run as integration tests."
)


def test_teacher_reads_student_attributes(page_login, teacher_login):
    """
    Tests: CP0005
    """
    page: Page = page_login(**teacher_login)
    page.goto("/univention/ucsschool/user-management/ui/")
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("Student")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("Max")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("max.student")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("Student (school1)")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("1a (school1)")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("school1")
    expect(page.get_by_label("Data table").locator("tbody")).to_contain_text("True")
    page.get_by_role("button", name="Student").click()
    expect(page.get_by_role("heading")).to_contain_text("Users (schools) > max.student")
    expect(page.get_by_label("School", exact=True)).to_have_value("school1")
    expect(page.get_by_label("Last name")).to_have_value("Student")
    expect(page.get_by_label("First name")).to_have_value("Max")
    expect(page.get_by_label("Username")).to_have_value("max.student")
    expect(page.get_by_label("Email")).to_have_value("max.student@school1.ucsschool.test")
    expect(page.get_by_label("Password")).to_be_empty()
    expect(page.get_by_label("Birthday")).to_have_value("This field is classified")
    expect(page.get_by_label("Expiration date")).to_have_value("This field is classified")
    expect(page.get_by_role("row", name="1a").get_by_role("checkbox")).to_be_checked()
    expect(page.get_by_role("row", name="2a").get_by_role("checkbox")).not_to_be_checked()
    expect(page.get_by_role("row", name="Student").get_by_role("checkbox")).to_be_checked()
    expect(page.get_by_role("row", name="Teacher").get_by_role("checkbox")).not_to_be_checked()
    expect(page.get_by_role("row", name="Staff").get_by_role("checkbox")).not_to_be_checked()
    expect(page.get_by_role("row", name="School Admin").get_by_role("checkbox")).not_to_be_checked()
    expect(page.get_by_label("Activated")).to_be_checked()


def test_teacher_cannot_read_student_from_other_school(page_login, teacher_login):
    """
    Tests: CP0006
    """
    page = page_login(**teacher_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school2").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_label("Data table").locator("tbody")).not_to_contain_text("laura.student")
    page.goto("/univention/ucsschool/user-management/ui/edit/laura.student?school=school2")
    expect(page.get_by_role("main")).to_contain_text("The user does not exist")


@pytest.mark.parametrize(
    "role,readable_attributes",
    [
        (
            "student",
            {
                "Username": "max.student",
                "First Name": "Max",
                "Last name": "Student",
                "Password": "This field is classified",
                "Email": "max.student@school1.ucsschool.test",
                "Birthday": "",
                "Expiration date": "",
            },
        ),
        (
            "teacher",
            {
                "Username": "mina.teacher",
                "First Name": "Mina",
                "Last name": "Teacher",
                "Password": "This field is classified",
                "Email": "mina.teacher@school1.ucsschool.test",
                "Birthday": "",
                "Expiration date": "",
            },
        ),
        (
            "staff",
            {
                "Username": "armin.staff",
                "First Name": "Armin",
                "Last name": "Staff",
                "Password": "This field is classified",
                "Email": "armin.staff@school1.ucsschool.test",
                "Birthday": "",
                "Expiration date": "",
            },
        ),
        (
            "school_admin",
            {
                "Username": "alex.admin",
                "First Name": "Alex",
                "Last name": "Admin",
                "Password": "This field is classified",
                "Email": "alex.admin@school1.ucsschool.test",
                "Birthday": "",
                "Expiration date": "",
            },
        ),
    ],
)
def test_has_read_permissions(page_login, role: str, readable_attributes: dict):
    """
    CP0001 - A Student can read its own attributes.
    CP0002 - A Teacher can read its own attributes.
    CP0003 - A Staff can read its own attributes.
    CP0004 - A SchoolAdmin can read its own attributes.
    """

    username = readable_attributes["Username"]  # nosec
    page: Page = page_login(password="univention", username=username)  # nosec

    page.goto(f"/univention/ucsschool/user-management/ui/edit/{username}?school=school1")

    for key, value in readable_attributes.items():
        element = page.get_by_label(key)
        expect(element).to_be_visible()
        expect(element).to_have_value(value)

    expect(page.get_by_role("row", name="1a").get_by_role("checkbox")).to_be_checked(
        checked=role in ["student", "teacher"]
    )
    expect(page.get_by_role("row", name="2a").get_by_role("checkbox")).to_be_checked(checked=False)
    expect(page.get_by_role("row", name="Student").get_by_role("checkbox")).to_be_checked(
        checked=role == "student"
    )
    expect(page.get_by_role("row", name="Teacher").get_by_role("checkbox")).to_be_checked(
        checked=role == "teacher"
    )
    expect(page.get_by_role("row", name="Staff").get_by_role("checkbox")).to_be_checked(
        checked=role == "staff"
    )
    expect(page.get_by_role("row", name="School Admin").get_by_role("checkbox")).to_be_checked(
        checked=role == "school_admin"
    )
    expect(page.get_by_label("Activated")).to_be_checked()


@pytest.mark.asyncio
async def test_teacher_can_edit_password_of_student_in_same_school_class(
    page_login, teacher_login, kelvin_user_factory, context
):
    """
    Tests: CP0007
    """
    student: User = await kelvin_user_factory(
        school="school1", schools=["school1"], roles=["student"], school_classes={"school1": ["1a"]}
    )

    page: Page = page_login(**teacher_login)

    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text(student.name)).to_be_visible()
    page.get_by_role("button", name=student.lastname).click()

    page.get_by_label("Password").click()
    new_password = secrets.token_urlsafe(nbytes=15)
    page.get_by_label("Password").fill(new_password)
    page.get_by_label("Password").press("Enter")

    expect(page.get_by_role("heading", name="Management of school users")).to_be_visible()
    context.clear_cookies()
    page_login(student.name, new_password)


@pytest.mark.parametrize(
    "school,school_classes",
    [
        ("school1", {"school1": ["2a"]}),
        ("school2", {"school2": ["1a"]}),
    ],
)
@pytest.mark.asyncio
async def test_teacher_cannot_edit_password_of_student_in_other_school_class(
    page_login, teacher_login, kelvin_user_factory, school, school_classes
):
    """
    Tests: CP0008
    """
    student: User = await kelvin_user_factory(
        school="school1", schools=[school], roles=["student"], school_classes=school_classes
    )
    page: Page = page_login(**teacher_login)

    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school2").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text(student.name)).not_to_be_visible()
    expect(page.get_by_label("Data table").locator("tbody")).not_to_contain_text(student.name)


@pytest.mark.parametrize("role", ["Student", "Teacher"])
def test_school_admin_can_create_user_in_own_school(page_login, admin_login, kelvin_user_deletion, role):
    """
    Tests: CP0009
    """
    kelvin_user_deletion("new.testuser")
    page: Page = page_login(**admin_login)
    page.goto("/univention/ucsschool/user-management/ui/")
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Max")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Muster")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("new.testuser")
    page.get_by_role("row", name=role).get_by_role("checkbox").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_label("Activated").click()
    page.get_by_role("button", name="Create user").click()
    page.get_by_role("heading", name="The user 'new.testuser' was").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text("new.testuser")).to_be_visible()


@pytest.mark.parametrize("role", ["Student", "Teacher"])
def test_school_admin_cannot_create_user_in_other_school(page_login, admin_login, role):
    """
    Tests: CP0010
    """
    page: Page = page_login(**admin_login)
    page.goto("/univention/ucsschool/user-management/ui/add?school=school2")
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Lastname")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Firstname")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("firstname.lastname")
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("row", name=role).get_by_role("checkbox").click()
    page.get_by_role("button", name="Create user").click()
    expect(page.get_by_role("heading", name="The user could not be created")).to_contain_text(
        "The user could not be created"
    )
    expect(page.get_by_text("You do not have the permission to create this user.")).to_contain_text(
        "You do not have the permission to create this user."
    )


@pytest.mark.parametrize(
    "role",
    [
        "student",
        "teacher",
        pytest.param(
            "staff", marks=[pytest.mark.xfail(reason="TBD: how to handle user without class?")]
        ),
    ],
)
@pytest.mark.asyncio
async def test_school_admin_can_edit_any_attribute_of(
    page_login, admin_login, role, kelvin_user_factory, faker, kelvin_user_deletion
):
    """
    Tests: CP0011-CP0013
    """
    target_user: User = await kelvin_user_factory(
        school="school1",
        schools=["school1"],
        roles=[role],
        school_classes={"school1": ["1a"]},
    )
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text(target_user.name)).to_be_visible()
    page.get_by_role("button", name=target_user.lastname).click()
    expect(page.get_by_label("School", exact=True)).to_be_visible()
    expect(page.get_by_text("School(readonly)")).to_be_visible()
    expect(page.get_by_label("Birthday")).to_be_visible()
    expect(page.get_by_text("Birthday(readonly)")).to_be_visible()
    expect(page.get_by_label("Expiration date")).to_be_visible()
    expect(page.get_by_text("Expiration date(readonly)")).to_be_visible()
    page.get_by_label("Last name").click()
    first_name = faker.first_name()
    last_name = faker.last_name()
    page.get_by_label("Last name").fill(last_name)
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill(first_name)
    new_username = f"{first_name}.{last_name}"
    kelvin_user_deletion(new_username)
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill(new_username)
    page.get_by_label("Email").click()
    page.get_by_label("Email").fill(f"{new_username}@school1.ucsschool.test")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill(secrets.token_urlsafe(nbytes=15))
    page.get_by_label("Password").press("Enter")
    expect(page.get_by_role("heading", name="Management of school users")).to_be_visible()
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a", exact=True).get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text(new_username)).to_be_visible()


@pytest.mark.parametrize("role", ["student", "teacher", "staff"])
@pytest.mark.asyncio
async def test_school_admin_follow_link_to_edit_page(page_login, role, kelvin_user_factory):
    """
    Tests: A0004
    """
    target_user: User = await kelvin_user_factory(
        school="school1",
        schools=["school1"],
        roles=[role],
        school_classes={"school1": ["1a"]},
    )
    page: Page = page_login("alex.admin", "univention")
    page.goto(f"/univention/ucsschool/user-management/ui/edit/{target_user.name}?school=school1")


@pytest.mark.asyncio
async def test_school_admin_cant_edit_any_attribute_of_school_admin(
    page_login, admin_login, kelvin_user_factory
):
    """
    Tests: CP0014
    """
    target_user: User = await kelvin_user_factory(
        school="school1", schools=["school1"], roles=["school_admin"], school_classes={"school1": ["1a"]}
    )
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_role("gridcell", name=target_user.name)).to_have_count(0)
    # row is not there, try navigating directly
    page.goto(f"/univention/ucsschool/user-management/ui/edit/{target_user.name}?school=school1")
    # We can navigate to the page, but can't see anything.
    expect(page.get_by_label("School", exact=True)).to_have_count(0)
    expect(page.get_by_label("Username")).to_have_count(0)


@pytest.mark.parametrize(
    "role",
    [
        "student",
        "teacher",
        pytest.param(
            "staff", marks=[pytest.mark.xfail(reason="TBD: how to handle user without class?")]
        ),
    ],
)
@pytest.mark.asyncio
async def test_school_admin_cant_edit_any_attribute_of_users_in_other_schools(
    page_login, admin_login, kelvin_user_factory, role
):
    """
    Tests: CP0015
    """
    other_school = "school2"
    target_user: User = await kelvin_user_factory(
        school=other_school, schools=[other_school], roles=[role], school_classes={other_school: ["1a"]}
    )
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name=other_school).click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_role("gridcell", name=target_user.name)).to_have_count(0)
    # row is not there, try navigating directly
    page.goto(
        f"/univention/ucsschool/user-management/ui/edit/" f"{target_user.name}?school={other_school}"
    )
    # We can navigate to the page, but can't see anything.
    expect(page.get_by_label("School", exact=True)).to_have_count(0)
    expect(page.get_by_label("Username")).to_have_count(0)


@pytest.mark.parametrize(
    "role",
    [
        "student",
        "teacher",
        pytest.param(
            "staff", marks=[pytest.mark.xfail(reason="TBD: how to handle user without class?")]
        ),
    ],
)
@pytest.mark.asyncio
async def test_school_admin_can_delete_users_of_same_school(
    page_login, admin_login, role, kelvin_user_factory
):
    """
    Tests: CP0016
    delete of school_admins is covered by test_school_admin_cant_edit_any_attribute_of_school_admin
    """
    target_user: User = await kelvin_user_factory(
        school="school1", schools=["school1"], roles=[role], school_classes={"school1": ["1a"]}
    )
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_role("gridcell", name=target_user.name)).to_be_visible()
    page.get_by_role("gridcell", name=target_user.name).locator("..").get_by_role("checkbox").click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_label("Delete user").get_by_role("button", name="Delete").click()
    # -> User is removed and thus not visible anymore.
    expect(page.get_by_role("gridcell", name=target_user.name)).to_have_count(0)


@pytest.mark.parametrize(
    "role",
    [
        "student",
        "teacher",
        pytest.param(
            "staff", marks=[pytest.mark.xfail(reason="TBD: how to handle user without class?")]
        ),
    ],
)
@pytest.mark.asyncio
async def test_school_admin_cant_delete_users_of_other_schools(
    page_login, admin_login, role, kelvin_user_factory
):
    """
    Tests: CP0017
    """
    target_user: User = await kelvin_user_factory(
        school="school2", schools=["school2"], roles=[role], school_classes={"school2": ["1a"]}
    )
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school2").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_role("gridcell", name=target_user.name)).to_have_count(0)


@pytest.mark.parametrize("role", ["Student", "Teacher"])
def test_school_admin_create_users_without_school_classes(
    page_login, admin_login, kelvin_user_deletion, role
):
    """
    Tests: CP0018, CP0019
    """
    kelvin_user_deletion("new.testuser")
    page: Page = page_login(**admin_login)
    page.goto("/univention/ucsschool/user-management/ui/")
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Max")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Muster")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("new.testuser")
    page.get_by_role("row", name=role).get_by_role("checkbox").click()
    page.get_by_label("Activated").click()
    page.get_by_role("button", name="Create user").click()
    if role == "Student":
        expect(page.get_by_role("heading", name="The user could not be created")).to_be_visible(
            timeout=30000
        )
    elif role == "Teacher":
        page.get_by_role("heading", name="The user 'new.testuser' was").click()
        page.get_by_role("button", name="OK").click()
        # TBD: how to handle user without class? Will never be visible
        # expect(page.get_by_text("new.testuser")).to_be_visible()
    else:
        raise ValueError("Invalid role.")


def test_school_admin_create_multi_role_user(page_login, admin_login, kelvin_user_deletion):
    """
    Tests: CP0020
    """
    kelvin_user_deletion("new.testuser")
    page: Page = page_login(**admin_login)
    page.goto("/univention/ucsschool/user-management/ui/")
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Max")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Muster")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("new.testuser")
    page.get_by_role("row", name="Student").get_by_role("checkbox").click()
    page.get_by_role("row", name="Teacher").get_by_role("checkbox").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_label("Activated").click()
    page.get_by_role("button", name="Create user").click()
    page.get_by_role("heading", name="The user 'new.testuser' was").click()
    page.get_by_role("button", name="OK").click()
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    expect(page.get_by_text("new.testuser")).to_be_visible()


def test_module_is_not_accessible_by_non_ucsschool_users(page):
    """
    Tests: A0001
    """
    page.goto("/univention/ucsschool/user-management/ui/")
    page.get_by_label("Username or email").fill("Administrator")
    page.get_by_label("Password", exact=True).fill("univention")
    page.get_by_label("Password", exact=True).press("Enter")
    expect(page.get_by_role("heading", name="Users (schools)")).to_have_count(0, timeout=10000)
