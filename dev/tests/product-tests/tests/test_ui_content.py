# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
from playwright.sync_api import expect, Page


def test_add_button_enabled_status(page_login, admin_login):
    """
    Tests U0001
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    expect(page.get_by_role("button", name="Add")).to_be_enabled()
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school2").click()
    expect(page.get_by_role("button", name="Add")).to_be_disabled()


@pytest.mark.xfail(reason="TBD: how to handle user without class?")
def test_delete_button_enabled_status(page_login, admin_login):
    """
    Tests U0003
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Filter").click()
    page.get_by_role("row", name="Admin Alex alex.admin School").get_by_role("checkbox").click()
    expect(page.get_by_role("button", name="Delete")).to_be_disabled()
    page.get_by_role("row", name="Staff Armin armin.staff Staff").get_by_role("checkbox").click()
    expect(page.get_by_role("button", name="Delete")).to_be_enabled()


def test_school_prefilled_on_creation(page_login, admin_login):
    """
    Tests U0004
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    expect(page.get_by_label("School", exact=True)).to_have_value("school1")


@pytest.mark.xfail(reason="TBD: how to handle user without class?")
def test_values_prefilled_on_edit(page_login, admin_login):
    """
    Tests U0005
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Filter").click()
    page.get_by_role("button", name="Admin").click()
    expect(page.get_by_label("School", exact=True)).to_have_value("school1")
    expect(page.get_by_label("Last name")).to_have_value("Admin")
    expect(page.get_by_label("First name")).to_have_value("Alex")
    expect(page.get_by_label("Username")).to_have_value("alex.admin")
    expect(page.get_by_label("Email")).to_have_value("alex.admin@school1.ucsschool.test")


def test_creation_abort_dialog_if_data_entered(page_login, admin_login):
    """
    Tests U0006
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Muster")
    page.get_by_role("button", name="Back").click()
    expect(page.get_by_text("Do you want to cancel the creation dialog")).to_contain_text(
        "Do you want to cancel the creation dialog"
    )


def test_edit_abort_dialog_if_data_changed(page_login, admin_login):
    """
    Tests U0006
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    page.get_by_role("button", name="Student").click()
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("pwd")
    page.get_by_role("button", name="Back").click()
    expect(page.get_by_text("There are unsaved changes.")).to_contain_text("There are unsaved changes.")


def test_creation_dialog_abort_no_data_entered(page_login, admin_login):
    """
    Tests U0007
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_role("button", name="Back").click()
    expect(page.get_by_text("Do you want to cancel the creation dialog")).to_have_count(0)


def test_edit_abort_dialog_if_no_data_changed(page_login, admin_login):
    """
    Tests U0007
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("button", name="Filter").click()
    page.get_by_role("button", name="Student").click()
    page.get_by_role("button", name="Back").click()
    expect(page.get_by_text("There are unsaved changes.")).to_have_count(0)


def test_frontend_validation_for_required_fields(page_login, admin_login):
    """
    Tests U0008
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_role("button", name="Create user").click()
    expect(page.get_by_text("Error: This value is required")).to_have_count(4)


def test_backend_validation(page_login, admin_login):
    """
    Tests U0008, U0009
    """
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Muster")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Max")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("max.muster")
    page.get_by_role("row", name="Student").get_by_role("checkbox").click()
    page.get_by_role("button", name="Create user").click()
    expect(
        page.get_by_text(
            "Some fields contain errors:general: A student must be member of at least one school class."
        )
    ).to_be_visible()


def test_creation_notification(page_login, admin_login, kelvin_user_deletion):
    """
    Tests U0011
    """
    kelvin_user_deletion("max.muster")
    page: Page = page_login(**admin_login)
    page.get_by_role("button", name="Show options").click()
    page.get_by_role("option", name="school1").click()
    page.get_by_role("button", name="Add").click()
    page.get_by_label("Last name").click()
    page.get_by_label("Last name").fill("Muster")
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Max")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("max.muster")
    page.get_by_role("row", name="1a").get_by_role("checkbox").click()
    page.get_by_role("row", name="Student").get_by_role("checkbox").click()
    page.get_by_role("button", name="Create user").click()
    expect(
        page.get_by_role("heading", name="The user 'max.muster' was successfully created")
    ).to_be_visible()


@pytest.mark.skip(reason="Not implemented yet.")
def test_modification_notification():
    """
    Tests U0012
    """
    raise AssertionError("This does currently not exist.")
