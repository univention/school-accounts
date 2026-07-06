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
from urllib.parse import quote

from .constants import FRONTEND_PREFIX
from .lang import _
from .models import (
    AttributeAccess,
    Permission,
    School,
    SchoolClass,
    User,
    UserAttributes,
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
    permissions: dict[str, list[Permission]]


@dataclass
class UserDetailData:
    user: User
    # The school context the detail view is scoped to (drives the patch route).
    school: str
    schools: list[School]
    school_classes: dict[str, list[SchoolClass]]
    work_groups: dict[str, list[WorkGroup]]
    permissions: set[Permission]


# ---------------------------------------------------------------------------
# View models consumed by the templates
# ---------------------------------------------------------------------------
@dataclass
class Option:
    value: str
    label: str
    selected: bool = False


@dataclass
class SchoolOption(Option):
    # School-context "create-user" permission; drives the future Add button.
    can_add: bool = False


@dataclass
class Column:
    label: str
    kind: str  # "text" | "list" | "boolean"


@dataclass
class Cell:
    # ``visible`` is False when the actor has no read/write access to the
    # attribute, in which case the template renders nothing.
    visible: bool
    kind: str
    text: str | None = None
    items: list[str] = field(default_factory=list)
    activated: bool | None = None
    # Set on the username cell so the template links it to the detail view.
    href: str | None = None


@dataclass
class Row:
    id: str
    cells: list[Cell]
    can_delete: bool


@dataclass
class UserListView:
    columns: list[Column]
    rows: list[Row]


@dataclass
class DetailField:
    name: str
    label: str
    # "text" | "email" | "password" | "date" | "boolean" | "list"
    kind: str
    # WRITE attributes render an editable control; READ attributes render a
    # disabled/static field. NONE attributes stay in the view (see ``accessible``)
    # but never carry a value/control.
    editable: bool
    # False when the actor has no read/write access: the row is still rendered,
    # but with a "no access" badge instead of a value or control.
    accessible: bool = True
    value: str | None = None
    items: list[str] = field(default_factory=list)
    activated: bool | None = None
    text: str | None = None
    # Inline validation error shown on the field after a rejected patch.
    error: str | None = None
    # The control the template renders for this field. Computed here so the
    # template stays a flat dispatch instead of re-deriving the same decision
    # from ``accessible``/``editable``/``kind``/``value``. One of:
    # "no_access" | "input" | "static" | "checkbox" | "boolean_badge" | "list" | "empty".
    widget: str = "empty"


@dataclass
class UserDetailView:
    id: str
    school: str
    title: str
    fields: list[DetailField]
    # True when the actor can write at least one attribute (drives the Save button).
    any_writable: bool


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
def build_school_options(data: SchoolsData, query: str = "") -> list[SchoolOption]:
    needle = query.strip().casefold()
    return [
        SchoolOption(
            value=school.id,
            label=school.display_name,
            can_add=Permission.create_user in set(data.permissions.get(school.id, [])),
        )
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


def empty_user_list_view(lang: str) -> UserListView:
    return UserListView(columns=list_columns(lang), rows=[])


def list_columns(lang: str) -> list[Column]:
    return [
        Column(label=_("Last name", lang=lang), kind="text"),
        Column(label=_("First name", lang=lang), kind="text"),
        Column(label=_("Username", lang=lang), kind="text"),
        Column(label=_("Roles", lang=lang), kind="list"),
        Column(label=_("Classes", lang=lang), kind="list"),
        Column(label=_("Work Groups", lang=lang), kind="list"),
        Column(label=_("Schools", lang=lang), kind="list"),
        Column(label=_("Activated", lang=lang), kind="boolean"),
    ]


def build_user_list(data: UserListData, lang: str, school: str) -> UserListView:
    rows: list[Row] = []
    for user in data.users:
        permissions = set(data.permissions.get(user.id, []))
        # A user is only listed if the actor holds at least one permission on
        # them (``username`` alone is implicit and never produced in isolation).
        if not permissions:
            continue
        attributes = user.attributes
        # The username cell links into the detail view, scoped to the searched school.
        username_cell = _text_cell("username", attributes.username, permissions)
        username_cell.href = f"{FRONTEND_PREFIX}/users/{quote(user.id)}?school={quote(school)}"
        cells = [
            _text_cell("last_name", attributes.last_name, permissions),
            _text_cell("first_name", attributes.first_name, permissions),
            username_cell,
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
        rows.append(Row(id=user.id, cells=cells, can_delete=Permission.delete_user in permissions))
    return UserListView(columns=list_columns(lang), rows=rows)


def _user_title(attributes: UserAttributes, permissions: set[Permission]) -> str:
    """A friendly heading from the readable name parts, falling back to the username."""

    def readable(name: str) -> bool:
        return _attribute_access(name, permissions) is not AttributeAccess.NONE

    parts = []
    if readable("first_name") and attributes.first_name:
        parts.append(attributes.first_name)
    if readable("last_name") and attributes.last_name:
        parts.append(attributes.last_name)
    return " ".join(parts) if parts else attributes.username


def build_user_detail(data: UserDetailData, lang: str) -> UserDetailView:
    """Shape a single user into the combined detail/edit view model.

    Every attribute is resolved against the actor's permissions and always
    rendered: WRITE becomes an editable field, READ a read-only field, NONE a
    row flagged not ``accessible`` (a "no access" badge in the template).
    Relational attributes are read-only this epic. Empty readable values render
    as ``n.a.`` in the template.
    """
    attributes = data.user.attributes
    permissions = data.permissions
    fields: list[DetailField] = []

    def scalar(name: str, label: str, kind: str, value: str | None) -> None:
        access = _attribute_access(name, permissions)
        accessible = access is not AttributeAccess.NONE
        editable = access is AttributeAccess.WRITE
        # Never expose a value the actor cannot read.
        field_value = value if accessible else None
        if not accessible:
            widget = "no_access"
        elif editable:
            widget = "input"
        elif field_value:
            widget = "static"
        else:
            widget = "empty"
        fields.append(
            DetailField(
                name=name,
                label=_(label, lang=lang),
                kind=kind,
                editable=editable,
                accessible=accessible,
                value=field_value,
                widget=widget,
            )
        )

    scalar("last_name", "Last name", "text", attributes.last_name)
    scalar("first_name", "First name", "text", attributes.first_name)
    scalar("username", "Username", "text", attributes.username)
    scalar("email", "Email", "email", attributes.email)
    # Password is write-only: never displayed, so it only appears when writable.
    scalar("password", "Password", "password", "")
    scalar(
        "birthday",
        "Birthday",
        "date",
        attributes.birthday.isoformat() if attributes.birthday else None,
    )
    scalar(
        "expiration_date",
        "Expiration date",
        "date",
        attributes.expiration_date.isoformat() if attributes.expiration_date else None,
    )

    activated_access = _attribute_access("activated", permissions)
    activated_accessible = activated_access is not AttributeAccess.NONE
    activated_editable = activated_access is AttributeAccess.WRITE
    activated = not attributes.disabled
    if not activated_accessible:
        activated_widget = "no_access"
    elif activated_editable:
        activated_widget = "checkbox"
    else:
        activated_widget = "boolean_badge"
    fields.append(
        DetailField(
            name="activated",
            label=_("Activated", lang=lang),
            kind="boolean",
            editable=activated_editable,
            accessible=activated_accessible,
            activated=activated if activated_accessible else None,
            text=(
                (_("Activated", lang=lang) if activated else _("Deactivated", lang=lang))
                if activated_accessible
                else None
            ),
            widget=activated_widget,
        )
    )

    def relational(name: str, label: str, item_builder) -> None:
        # Relational attributes are read-only this epic (editable=False).
        access = _attribute_access(name, permissions)
        accessible = access is not AttributeAccess.NONE
        items = item_builder() if accessible else []
        if not accessible:
            widget = "no_access"
        elif items:
            widget = "list"
        else:
            widget = "empty"
        fields.append(
            DetailField(
                name=name,
                label=_(label, lang=lang),
                kind="list",
                editable=False,
                accessible=accessible,
                items=items,
                widget=widget,
            )
        )

    relational("roles", "Roles", lambda: [_format_role(data.schools, r, lang) for r in attributes.roles])
    relational(
        "school_classes",
        "Classes",
        lambda: [
            _format_school_class(data.schools, data.school_classes[school], school, school_class)
            for school, classes in attributes.school_classes.items()
            for school_class in classes
        ],
    )
    relational(
        "work_groups",
        "Work Groups",
        lambda: [
            _format_work_group(data.schools, data.work_groups[school], school, work_group)
            for school, groups in attributes.work_groups.items()
            for work_group in groups
        ],
    )
    relational(
        "schools", "Schools", lambda: [_format_school(data.schools, s) for s in attributes.schools]
    )

    return UserDetailView(
        id=data.user.id,
        school=data.school,
        title=_user_title(attributes, permissions),
        fields=fields,
        any_writable=any(field.editable for field in fields),
    )
