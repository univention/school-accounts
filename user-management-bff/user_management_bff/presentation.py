# Copyright (C) 2026 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Presentation helpers for the server-rendered UI.

Pure functions that turn the raw domain data returned by ``business_logic`` into
view models the Jinja templates iterate over. This keeps permission resolution
and display formatting out of the templates without reintroducing a
representation port/adapter.
"""
from collections.abc import Collection
from dataclasses import dataclass, field

from .lang import _
from .models import (
    AttributeAccess,
    Permission,
    School,
    SchoolClass,
    User,
    WorkGroup,
)


# ---------------------------------------------------------------------------
# Raw data bundles returned by ``business_logic`` (input to the builders below)
# ---------------------------------------------------------------------------
@dataclass
class UserListData:
    users: list[User]
    schools: list[School]
    school_classes: dict[str, list[SchoolClass]]
    work_groups: dict[str, list[WorkGroup]]
    permissions: dict[str, list[Permission]]


@dataclass
class SchoolsData:
    schools: list[School]


# ---------------------------------------------------------------------------
# View models consumed by the templates
# ---------------------------------------------------------------------------
@dataclass
class Option:
    value: str
    label: str
    selected: bool = False


@dataclass
class OptionGroup:
    heading: str
    options: list[Option]


@dataclass
class Column:
    label: str


@dataclass
class Cell:
    # ``visible`` is False when the actor has no read/write access to the
    # attribute, in which case the template renders nothing.
    visible: bool
    kind: str
    text: str | None = None
    items: list[str] = field(default_factory=list)
    activated: bool | None = None


@dataclass
class Row:
    cells: list[Cell]


@dataclass
class UserListView:
    columns: list[Column]
    rows: list[Row]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _attribute_access(name: str, permissions: set[Permission]) -> AttributeAccess:
    """Resolve an attribute's access level from the actor's permissions.

    ``username`` is always readable; a matching ``write-*`` permission upgrades
    ``read`` to ``write``. Names without a corresponding permission member
    simply stay ``NONE`` (the ``Permission(...)`` lookup raises ``ValueError``).
    """
    access = AttributeAccess.READ if name == "username" else AttributeAccess.NONE
    try:
        if Permission(f"read-{name}") in permissions:
            access = AttributeAccess.READ
    except ValueError:
        pass
    try:
        if Permission(f"write-{name}") in permissions:
            access = AttributeAccess.WRITE
    except ValueError:
        pass
    return access


def _find_by_id(items, item_id: str):
    return next((item for item in items if item.id == item_id), None)


def _format_school(schools: list[School], school_id: str) -> str:
    return _find_by_id(schools, school_id).display_name


def _format_school_class(
    schools: list[School], classes: list[SchoolClass], school_id: str, class_id: str
) -> str:
    school = _find_by_id(schools, school_id)
    school_class = _find_by_id(classes, class_id)
    return f"{school_class.display_name} ({school.display_name})"


def _format_work_group(
    schools: list[School], work_groups: list[WorkGroup], school_id: str, work_group_id: str
) -> str:
    school = _find_by_id(schools, school_id)
    work_group = _find_by_id(work_groups, work_group_id)
    return f"{work_group.display_name} ({school.display_name})"


def _format_role(schools: list[School], role: str, lang: str) -> str:
    school = _find_by_id(schools, role.rsplit(":", 1)[1])
    role_str = role.replace("_", " ").split(":", 1)[0].title()
    return f"{_(role_str, lang=lang)} ({school.display_name})"


def _text_cell(name: str, value: str | None, permissions: set[Permission]) -> Cell:
    visible = _attribute_access(name, permissions) is not AttributeAccess.NONE
    return Cell(visible=visible, kind="text", text=value)


def _list_cell(name: str, items: list[str], permissions: set[Permission]) -> Cell:
    visible = _attribute_access(name, permissions) is not AttributeAccess.NONE
    return Cell(visible=visible, kind="list", items=items if visible else [])


def _boolean_cell(name: str, activated: bool, permissions: set[Permission], lang: str) -> Cell:
    visible = _attribute_access(name, permissions) is not AttributeAccess.NONE
    return Cell(
        visible=visible,
        kind="boolean",
        activated=activated,
        text=_("Activated", lang=lang) if activated else _("Deactivated", lang=lang),
    )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
# Classes and work groups share one filter control, so their option values are
# prefixed with the kind they came from and split apart again server-side.
SCHOOL_CLASS_KIND = "school_class"
WORK_GROUP_KIND = "work_group"
# The control is single-select and always has a selection, so "no group filter"
# needs a value of its own rather than being the absence of one.
ALL_GROUPS = "all"


def build_school_options(data: SchoolsData, query: str = "", selected: str = "") -> list[Option]:
    needle = query.strip().casefold()
    return [
        Option(value=school.id, label=school.display_name, selected=school.id == selected)
        for school in sorted(data.schools, key=lambda s: s.display_name)
        if needle in school.display_name.casefold()
    ]


def build_options(
    items: list[SchoolClass] | list[WorkGroup],
    selected: Collection[str] = (),
    query: str = "",
) -> list[Option]:
    selected_ids = set(selected)
    needle = query.strip().casefold()
    return [
        Option(value=item.id, label=item.display_name, selected=item.id in selected_ids)
        for item in sorted(items, key=lambda i: i.display_name)
        if needle in item.display_name.casefold()
    ]


def split_group_value(value: str | None) -> tuple[str, str]:
    """Split a combined ``kind:id`` filter value into its two parts.

    Anything that is not a known kind yields ``("", "")``, so a stale or
    hand-edited deep link degrades to "no group filter" instead of erroring.
    Only the first colon separates, leaving ids that contain one intact.
    """
    kind, _sep, item_id = (value or "").partition(":")
    if kind not in (SCHOOL_CLASS_KIND, WORK_GROUP_KIND) or not item_id:
        return "", ""
    return kind, item_id


def build_group_options(
    school_classes: list[SchoolClass],
    work_groups: list[WorkGroup],
    lang: str,
    selected: str = "",
    query: str = "",
) -> list[OptionGroup]:
    """Build the sections of the combined class/work-group filter.

    Both datasets feed a single-select control, so each value carries its kind as
    a prefix; ``selected`` is such a prefixed value.
    """
    groups: list[OptionGroup] = []
    for kind, heading, items in (
        (SCHOOL_CLASS_KIND, _("Classes", lang=lang), school_classes),
        (WORK_GROUP_KIND, _("Work Groups", lang=lang), work_groups),
    ):
        options: list[Option] = []
        for option in build_options(items, query=query):
            value = f"{kind}:{option.value}"
            options.append(Option(value=value, label=option.label, selected=value == selected))
        groups.append(OptionGroup(heading=heading, options=options))
    return groups


def empty_user_list_view(lang: str) -> UserListView:
    return UserListView(columns=list_columns(lang), rows=[])


def list_columns(lang: str) -> list[Column]:
    return [
        Column(label=_("Last name", lang=lang)),
        Column(label=_("First name", lang=lang)),
        Column(label=_("Username", lang=lang)),
        Column(label=_("Roles", lang=lang)),
        Column(label=_("Classes", lang=lang)),
        Column(label=_("Work Groups", lang=lang)),
        Column(label=_("Schools", lang=lang)),
        Column(label=_("Activated", lang=lang)),
    ]


def build_user_list(data: UserListData, lang: str) -> UserListView:
    rows: list[Row] = []
    for user in data.users:
        permissions = set(data.permissions.get(user.id, []))
        # A user is only listed if the actor holds at least one permission on
        # them (``username`` alone is implicit and never produced in isolation).
        if not permissions:
            continue
        attributes = user.attributes
        cells = [
            _text_cell("last_name", attributes.last_name, permissions),
            _text_cell("first_name", attributes.first_name, permissions),
            _text_cell("username", attributes.username, permissions),
            _list_cell(
                "roles",
                [_format_role(data.schools, role, lang) for role in attributes.roles],
                permissions,
            ),
            _list_cell(
                "school_classes",
                [
                    _format_school_class(data.schools, data.school_classes[school], school, school_class)
                    for school, classes in attributes.school_classes.items()
                    for school_class in classes
                ],
                permissions,
            ),
            _list_cell(
                "work_groups",
                [
                    _format_work_group(data.schools, data.work_groups[school], school, work_group)
                    for school, groups in attributes.work_groups.items()
                    for work_group in groups
                ],
                permissions,
            ),
            _list_cell(
                "schools",
                [_format_school(data.schools, school) for school in attributes.schools],
                permissions,
            ),
            _boolean_cell("activated", not attributes.disabled, permissions, lang),
        ]
        rows.append(Row(cells=cells))
    return UserListView(columns=list_columns(lang), rows=rows)
