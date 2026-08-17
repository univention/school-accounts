# SPDX-FileCopyrightText: 2026 Univention GmbH
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
        ("first_name", set(), AttributeAccess.NONE),
        ("first_name", {Permission.read_first_name}, AttributeAccess.READ),
        ("password", set(), AttributeAccess.NONE),
        ("password", {Permission.write_password}, AttributeAccess.WRITE),
        (
            "first_name",
            {Permission.read_first_name, Permission.write_password},
            AttributeAccess.READ,  # an unrelated write permission doesn't upgrade a different field
        ),
        ("nonexistent", {Permission.read_first_name}, AttributeAccess.NONE),  # ValueError branches
    ],
)
def test_attribute_access(name: str, permissions: set[Permission], expected: AttributeAccess):
    assert presentation._attribute_access(name, permissions) is expected


def test_find_by_id_missing_raises_keyerror():
    with pytest.raises(KeyError, match="Item with id missing not found"):
        presentation._find_by_id([School(id="a", display_name="Alpha")], "missing")


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


def test_build_school_options_marks_selected():
    data = presentation.SchoolsData(
        schools=[School(id="a", display_name="Alpha"), School(id="b", display_name="Beta")]
    )
    options = presentation.build_school_options(data, selected="b")
    assert {o.value: o.selected for o in options} == {"a": False, "b": True}


@pytest.mark.parametrize(
    "value,expected",
    [
        ("school_class:1a", ("school_class", "1a")),
        ("work_group:w1a", ("work_group", "w1a")),
        ("school_class:a:b", ("school_class", "a:b")),  # only the first colon separates
        (None, ("", "")),
        ("", ("", "")),
        ("1a", ("", "")),  # no separator
        ("school_class:", ("", "")),  # no id
        ("teacher:1a", ("", "")),  # unknown kind
        (presentation.ALL_GROUPS, ("", "")),  # the reset option means "no filter"
    ],
)
def test_split_group_value(value: str | None, expected: tuple[str, str]):
    assert presentation.split_group_value(value) == expected


def _group_sections():
    return (
        [
            SchoolClass(id="2b", display_name="2b", school="s"),
            SchoolClass(id="1a", display_name="1a", school="s"),
        ],
        [WorkGroup(id="w1a", display_name="w1a", school="s")],
    )


def test_build_group_options_prefixes_and_sorts():
    classes, work_groups = _group_sections()
    sections = presentation.build_group_options(classes, work_groups, "en")
    assert [s.heading for s in sections] == ["Classes", "Work Groups"]
    assert [o.value for o in sections[0].options] == ["school_class:1a", "school_class:2b"]
    assert [o.label for o in sections[0].options] == ["1a", "2b"]
    assert [o.value for o in sections[1].options] == ["work_group:w1a"]


def test_build_group_options_headings_are_translated():
    classes, work_groups = _group_sections()
    sections = presentation.build_group_options(classes, work_groups, "de")
    assert [s.heading for s in sections] == ["Klassen", "Arbeitsgruppen"]


def test_build_group_options_marks_selected_across_sections():
    classes, work_groups = _group_sections()
    sections = presentation.build_group_options(classes, work_groups, "en", selected="work_group:w1a")
    # The prefix is what disambiguates, so no class is selected by a bare id match.
    assert [o.selected for o in sections[0].options] == [False, False]
    assert [o.selected for o in sections[1].options] == [True]


def test_build_group_options_filters_both_sections_by_query():
    classes, work_groups = _group_sections()
    sections = presentation.build_group_options(classes, work_groups, "en", query="1a")
    assert [o.value for o in sections[0].options] == ["school_class:1a"]
    assert [o.value for o in sections[1].options] == ["work_group:w1a"]


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


def _user(**overrides: object) -> User:
    attributes = UserAttributes(
        last_name="Klein",
        first_name="Kim",
        username="kim",
        disabled=False,
        schools=["school1"],
        school_classes={"school1": ["1a"]},
        work_groups={"school1": ["w1a"]},
        roles=["teacher:school:school1"],
    )
    return User(id="u1", attributes=attributes.model_copy(update=overrides))


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


def test_build_password_reset_summary_all_succeeded():
    data = presentation.PasswordResetResultData(
        outcomes=[
            presentation.PasswordResetOutcome(
                target_id="user1", outcome=presentation.PasswordResetOutcomeCode.success
            ),
            presentation.PasswordResetOutcome(
                target_id="user2", outcome=presentation.PasswordResetOutcomeCode.success
            ),
        ]
    )
    message, variant = presentation.build_password_reset_summary(data, "en")
    assert message == "Password reset for 2 of 2 users."
    assert variant == "success"


def test_build_password_reset_summary_partial_failure():
    data = presentation.PasswordResetResultData(
        outcomes=[
            presentation.PasswordResetOutcome(
                target_id="user1", outcome=presentation.PasswordResetOutcomeCode.success
            ),
            presentation.PasswordResetOutcome(
                target_id="user2", outcome=presentation.PasswordResetOutcomeCode.permission_denied
            ),
        ]
    )
    message, variant = presentation.build_password_reset_summary(data, "en")
    assert message == "Password reset for 1 of 2 users."
    assert variant == "error"


@pytest.mark.parametrize(
    "code,expected_label",
    [
        (presentation.PasswordResetOutcomeCode.success, "Success"),
        (presentation.PasswordResetOutcomeCode.permission_denied, "Permission denied"),
        (presentation.PasswordResetOutcomeCode.not_found, "User not found"),
        (presentation.PasswordResetOutcomeCode.rejected, "Rejected"),
    ],
)
def test_build_password_reset_outcome_rows_labels(
    code: presentation.PasswordResetOutcomeCode, expected_label: str
):
    data = presentation.PasswordResetResultData(
        outcomes=[presentation.PasswordResetOutcome(target_id="user1", outcome=code)]
    )
    rows = presentation.build_password_reset_outcome_rows(data, "en")
    assert rows == [
        presentation.PasswordResetOutcomeRow(target_id="user1", label=expected_label, reason=None)
    ]


def test_build_password_reset_outcome_rows_carries_reason():
    data = presentation.PasswordResetResultData(
        outcomes=[
            presentation.PasswordResetOutcome(
                target_id="user1",
                outcome=presentation.PasswordResetOutcomeCode.rejected,
                reason="Password too short",
            )
        ]
    )
    rows = presentation.build_password_reset_outcome_rows(data, "en")
    assert rows == [
        presentation.PasswordResetOutcomeRow(
            target_id="user1", label="Rejected", reason="Password too short"
        )
    ]
