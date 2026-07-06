# Copyright (C) 2026 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Unit tests for the presentation view-model builders."""
import datetime

import pytest

from user_management_bff import presentation
from user_management_bff.constants import FRONTEND_PREFIX
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


def test_build_school_options_sorts_and_flags_add():
    data = presentation.SchoolsData(
        schools=[School(id="b", display_name="Beta"), School(id="a", display_name="Alpha")],
        permissions={"a": [Permission.create_user], "b": []},
    )
    options = presentation.build_school_options(data)
    assert [(o.value, o.label, o.can_add) for o in options] == [
        ("a", "Alpha", True),
        ("b", "Beta", False),
    ]


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
        ],
        permissions={"a": [], "b": []},
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


@pytest.mark.parametrize("lang", ["en", "de"])
def test_list_columns(lang):
    columns = presentation.list_columns(lang)
    assert [c.kind for c in columns] == [
        "text",
        "text",
        "text",
        "list",
        "list",
        "list",
        "list",
        "boolean",
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
    view = presentation.build_user_list(_list_data(_user(), list(Permission)), "en", "school1")
    row = view.rows[0]
    assert row.id == "u1"
    assert row.can_delete is True
    cells = row.cells
    assert cells[0].kind == "text" and cells[0].visible and cells[0].text == "Klein"
    assert cells[2].text == "kim"
    # The username cell links into the detail view, scoped to the searched school.
    assert cells[2].href == f"{FRONTEND_PREFIX}/users/u1?school=school1"
    assert cells[3].items == ["Teacher (School 1)"]
    assert cells[4].items == ["1a (School 1)"]
    assert cells[5].items == ["w1a (School 1)"]
    assert cells[6].items == ["School 1"]
    assert cells[7].kind == "boolean" and cells[7].activated is True and cells[7].text == "Activated"


def test_build_user_list_hidden_cells_and_deactivated():
    user = _user(disabled=True, school_classes={}, work_groups={}, roles=[])
    view = presentation.build_user_list(_list_data(user, [Permission.read_last_name]), "en", "school1")
    row = view.rows[0]
    assert row.can_delete is False
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
    view = presentation.build_user_list(data, "en", "school1")
    assert view.rows == []


# ---------------------------------------------------------------------------
# build_user_detail
# ---------------------------------------------------------------------------
def _detail_data(user: User, permissions, school: str = "school1") -> presentation.UserDetailData:
    return presentation.UserDetailData(
        user=user,
        school=school,
        schools=[School(id="school1", display_name="School 1")],
        school_classes={"school1": [SchoolClass(id="1a", display_name="1a", school="school1")]},
        work_groups={"school1": [WorkGroup(id="w1a", display_name="w1a", school="school1")]},
        permissions=set(permissions),
    )


def _field(view: presentation.UserDetailView, name: str) -> presentation.DetailField:
    return next(field for field in view.fields if field.name == name)


def test_build_user_detail_full_access():
    view = presentation.build_user_detail(_detail_data(_user(), set(Permission)), "en")
    assert view.id == "u1"
    assert view.school == "school1"
    assert view.title == "Kim Klein"
    assert view.any_writable is True
    assert [field.name for field in view.fields] == [
        "last_name",
        "first_name",
        "username",
        "email",
        "password",
        "birthday",
        "expiration_date",
        "activated",
        "roles",
        "school_classes",
        "work_groups",
        "schools",
    ]
    assert all(field.accessible for field in view.fields)
    assert _field(view, "last_name").editable is True and _field(view, "last_name").value == "Klein"
    # Writable scalars/booleans render editable controls; relational rows a list.
    assert _field(view, "last_name").widget == "input"
    assert _field(view, "activated").widget == "checkbox"
    assert _field(view, "roles").widget == "list"
    # An editable-but-unset scalar is still an input (not the empty badge).
    assert _field(view, "email").widget == "input"
    assert _field(view, "password").kind == "password" and _field(view, "password").value == ""
    # An unset readable value has no value (the template renders it as "n.a.").
    assert _field(view, "email").value is None
    # birthday is unset here -> the "else None" branch.
    assert _field(view, "birthday").value is None
    activated = _field(view, "activated")
    assert activated.kind == "boolean" and activated.activated is True and activated.text == "Activated"
    # Relational attributes are read-only this epic, formatted into display names.
    assert _field(view, "roles").editable is False
    assert _field(view, "roles").items == ["Teacher (School 1)"]
    assert _field(view, "school_classes").items == ["1a (School 1)"]
    assert _field(view, "work_groups").items == ["w1a (School 1)"]
    assert _field(view, "schools").items == ["School 1"]


def test_build_user_detail_read_only_and_title_fallback():
    # Only last_name is granted (READ); username is implicitly readable. Every other
    # attribute is NONE: the row is still present but flagged not accessible (the
    # template renders a "no access" badge), never carrying a value or control.
    view = presentation.build_user_detail(_detail_data(_user(), {Permission.read_last_name}), "en")
    # All attributes remain in the view regardless of access.
    assert [field.name for field in view.fields] == [
        "last_name",
        "first_name",
        "username",
        "email",
        "password",
        "birthday",
        "expiration_date",
        "activated",
        "roles",
        "school_classes",
        "work_groups",
        "schools",
    ]
    last_name = _field(view, "last_name")
    assert last_name.accessible is True and last_name.editable is False and last_name.value == "Klein"
    # A readable, non-writable scalar with a value renders as static text.
    assert last_name.widget == "static"
    assert _field(view, "username").accessible is True and _field(view, "username").editable is False
    # Not-readable attributes are flagged inaccessible with no leaked value/items.
    first_name = _field(view, "first_name")
    assert first_name.accessible is False and first_name.editable is False and first_name.value is None
    assert first_name.widget == "no_access"
    assert _field(view, "activated").accessible is False and _field(view, "activated").activated is None
    assert _field(view, "roles").accessible is False and _field(view, "roles").items == []
    assert view.any_writable is False
    # first_name is not readable, so the title falls back to the readable last name.
    assert view.title == "Klein"


def test_build_user_detail_title_falls_back_to_username():
    # Neither name part is readable -> the title is the (always readable) username.
    view = presentation.build_user_detail(_detail_data(_user(), set()), "en")
    assert view.title == "kim"


def test_build_user_detail_readonly_empty_and_boolean_badge_widgets():
    # Read-only access to attributes that carry no value: a readable-but-unset
    # scalar (email) and an empty relational (roles) both collapse to "empty";
    # a readable, non-writable boolean (activated) renders as a status badge.
    user = _user(roles=[])
    view = presentation.build_user_detail(
        _detail_data(user, {Permission.read_email, Permission.read_roles, Permission.read_activated}),
        "en",
    )
    assert _field(view, "email").accessible is True and _field(view, "email").widget == "empty"
    assert _field(view, "roles").accessible is True and _field(view, "roles").widget == "empty"
    activated = _field(view, "activated")
    assert activated.editable is False and activated.widget == "boolean_badge"


def test_build_user_detail_date_value_and_deactivated_badge():
    user = _user(disabled=True, birthday=datetime.date(2010, 5, 4))
    view = presentation.build_user_detail(
        _detail_data(user, {Permission.write_birthday, Permission.write_activated}), "en"
    )
    assert _field(view, "birthday").value == "2010-05-04"
    activated = _field(view, "activated")
    assert activated.editable is True
    assert activated.activated is False and activated.text == "Deactivated"
