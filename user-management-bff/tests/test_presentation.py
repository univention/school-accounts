# Copyright (C) 2026 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Unit tests for the presentation view-model builders."""
import pytest

from user_management_bff import presentation
from user_management_bff.models import (
    AttributeAccess,
    Permission,
    School,
    SchoolClass,
    User,
    UserAttributes,
    WorkGroup,
)


@pytest.mark.parametrize(
    "name,permissions,expected",
    [
        ("username", set(), AttributeAccess.READ),  # username is implicitly readable
        ("username", {Permission.write_username}, AttributeAccess.WRITE),
        ("first_name", set(), AttributeAccess.NONE),
        ("first_name", {Permission.read_first_name}, AttributeAccess.READ),
        ("first_name", {Permission.write_first_name}, AttributeAccess.WRITE),
        (
            "first_name",
            {Permission.read_first_name, Permission.write_first_name},
            AttributeAccess.WRITE,  # write upgrades read
        ),
        ("nonexistent", {Permission.read_first_name}, AttributeAccess.NONE),  # ValueError branches
    ],
)
def test_attribute_access(name, permissions, expected):
    assert presentation._attribute_access(name, permissions) is expected


def test_build_school_options_sorts_by_display_name():
    data = presentation.SchoolsData(
        schools=[School(id="b", display_name="Beta"), School(id="a", display_name="Alpha")]
    )
    options = presentation.build_school_options(data)
    assert [(o.value, o.label) for o in options] == [("a", "Alpha"), ("b", "Beta")]


def test_build_options_sorts_by_display_name():
    items = [
        SchoolClass(id="2b", display_name="2b", school="s"),
        SchoolClass(id="1a", display_name="1a", school="s"),
    ]
    assert [(o.value, o.label) for o in presentation.build_options(items)] == [
        ("1a", "1a"),
        ("2b", "2b"),
    ]


def test_build_options_marks_selected():
    items = [
        SchoolClass(id="1a", display_name="1a", school="s"),
        SchoolClass(id="2b", display_name="2b", school="s"),
    ]
    options = presentation.build_options(items, selected=["1a"])
    assert {o.value: o.selected for o in options} == {"1a": True, "2b": False}


def test_build_school_options_filters_by_query():
    data = presentation.SchoolsData(
        schools=[
            School(id="a", display_name="Alpha School"),
            School(id="b", display_name="Beta School"),
        ]
    )
    # Case-insensitive substring match on the display name.
    assert [o.value for o in presentation.build_school_options(data, query="  bEtA ")] == ["b"]
    # An empty query returns the full list.
    assert [o.value for o in presentation.build_school_options(data, query="")] == ["a", "b"]


def test_build_options_filters_by_query():
    items = [
        SchoolClass(id="1a", display_name="1a", school="s"),
        SchoolClass(id="2b", display_name="2b", school="s"),
    ]
    assert [o.value for o in presentation.build_options(items, query="2")] == ["2b"]


def test_list_columns_labels():
    assert [c.label for c in presentation.list_columns("en")] == [
        "Last name",
        "First name",
        "Username",
        "Roles",
        "Classes",
        "Work Groups",
        "Schools",
        "Activated",
    ]


def test_list_columns_are_translated():
    assert [c.label for c in presentation.list_columns("de")][:3] == [
        "Nachname",
        "Vorname",
        "Benutzername",
    ]


def _user(**overrides) -> User:
    attributes = dict(
        last_name="Klein",
        first_name="Kim",
        username="kim",
        disabled=False,
        schools=["school1"],
        school_classes={"school1": ["1a"]},
        work_groups={"school1": ["w1a"]},
        roles=["teacher:school:school1"],
    )
    attributes.update(overrides)
    return User(id="u1", attributes=UserAttributes(**attributes))


def _list_data(user: User, permissions: list[Permission]) -> presentation.UserListData:
    return presentation.UserListData(
        users=[user],
        schools=[School(id="school1", display_name="School 1")],
        school_classes={"school1": [SchoolClass(id="1a", display_name="1a", school="school1")]},
        work_groups={"school1": [WorkGroup(id="w1a", display_name="w1a", school="school1")]},
        permissions={user.id: permissions},
    )


def test_build_user_list_full_access():
    view = presentation.build_user_list(_list_data(_user(), list(Permission)), "en")
    cells = view.rows[0].cells
    assert cells[0].kind == "text" and cells[0].visible and cells[0].text == "Klein"
    assert cells[2].text == "kim"
    assert cells[3].items == ["Teacher (School 1)"]
    assert cells[4].items == ["1a (School 1)"]
    assert cells[5].items == ["w1a (School 1)"]
    assert cells[6].items == ["School 1"]
    assert cells[7].kind == "boolean" and cells[7].activated is True and cells[7].text == "Activated"


def test_build_user_list_hidden_cells_and_deactivated():
    user = _user(disabled=True, school_classes={}, work_groups={}, roles=[])
    view = presentation.build_user_list(_list_data(user, [Permission.read_last_name]), "en")
    row = view.rows[0]
    assert row.cells[0].visible is True  # last_name readable
    assert row.cells[1].visible is False  # first_name not granted
    assert row.cells[2].visible is True  # username implicitly readable
    assert row.cells[3].visible is False and row.cells[3].items == []  # roles hidden
    assert row.cells[7].activated is False and row.cells[7].text == "Deactivated"
    assert row.cells[7].visible is False


def test_build_user_list_skips_users_without_permissions():
    data = presentation.UserListData(
        users=[_user()], schools=[], school_classes={}, work_groups={}, permissions={}
    )
    view = presentation.build_user_list(data, "en")
    assert view.rows == []
