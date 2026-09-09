# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Presentation helpers for the server-rendered UI.

Pure functions that turn the raw domain data returned by ``business_logic`` into
view models the Jinja templates iterate over. This keeps permission resolution
and display formatting out of the templates without reintroducing a
representation port/adapter.
"""

from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Protocol, TypeVar

from .constants import (
    PASSWORD_RESET_BULK_THRESHOLD,
    PASSWORD_RESET_MAX_TARGETS,
    PASSWORD_RESET_NAMED_LIMIT,
)
from .lang import N_, _
from .models import (
    AttributeAccess,
    Permission,
    School,
    SchoolClass,
    User,
    WorkGroup,
)


class _HasId(Protocol):
    id: str


_Identifiable = TypeVar("_Identifiable", bound=_HasId)


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


class PasswordResetOutcomeCode(StrEnum):
    success = auto()
    permission_denied = auto()
    not_found = auto()
    rejected = auto()
    unconfirmed = auto()
    next_login_change_unsupported = auto()


class PasswordResetRequestError(StrEnum):
    """A whole-request validation failure - distinct from a per-target outcome.

    Set instead of populating ``outcomes`` at all: no targets selected, no
    password, or more targets than one request may carry.
    """

    no_targets = auto()
    empty_password = auto()
    too_many_targets = auto()


@dataclass
class PasswordResetSelectionData:
    """The selected users the actor may reset, plus how many were dropped.

    ``denied`` is reported rather than silently omitted: the confirmation step
    exists so the stated scope matches what the submit does.
    """

    users: list[User]
    denied: int = 0
    supports_change_on_next_login: bool = False
    request_error: PasswordResetRequestError | None = None


@dataclass
class PasswordResetOutcome:
    target_id: str
    outcome: PasswordResetOutcomeCode
    # Only ever set for ``rejected`` - the target system's own rejection reason,
    # normalized to a plain string by the adapter but otherwise unvetted (not
    # length-bounded). Never a translated string: the other codes carry no
    # dynamic detail, so they're conveyed by ``outcome`` alone.
    reason: str | None = None


@dataclass
class PasswordResetResultData:
    outcomes: list[PasswordResetOutcome]
    request_error: PasswordResetRequestError | None = None
    # What the write resolved, so re-rendering the dialog costs no second resolution.
    selection: PasswordResetSelectionData | None = None

    @property
    def password_rejection(self) -> str | None:
        """The reason, when every attempted write failed for the same one.

        One reason shared by every attempt is about the password, so it belongs on the
        field. A heuristic until the backend carries stable error codes (#231).
        """
        if any(outcome.outcome is PasswordResetOutcomeCode.success for outcome in self.outcomes):
            return None
        reasons = {
            outcome.reason
            for outcome in self.outcomes
            if outcome.outcome is PasswordResetOutcomeCode.rejected
        }
        return reasons.pop() if len(reasons) == 1 else None


@dataclass
class PasswordResetOutcomeRow:
    target_id: str
    label: str
    # The target system's own rejection reason - see ``PasswordResetOutcome.reason``.
    # Never translated, unlike ``label``.
    reason: str | None = None


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
    id: str
    cells: list[Cell]
    # Accessible name for the checkbox; not indexed out of ``cells``, so reordering
    # a column cannot relabel the control.
    label: str = ""
    selectable: bool = False


@dataclass
class UserListView:
    columns: list[Column]
    rows: list[Row]


@dataclass
class PasswordResetAccount:
    """One named account in the confirmation dialog."""

    name: str
    username: str


@dataclass
class RoleTally:
    label: str
    # A dual-role user counts under both, so tallies can exceed the total.
    count: int


@dataclass
class PasswordResetConfirmation:
    target_ids: list[str]
    accounts: list[PasswordResetAccount]
    role_tallies: list[RoleTally]
    denied: int = 0
    supports_change_on_next_login: bool = False

    @property
    def count(self) -> int:
        return len(self.target_ids)

    @property
    def mixed_roles(self) -> bool:
        return len(self.role_tallies) > 1

    @property
    def bulk(self) -> bool:
        return self.count > PASSWORD_RESET_BULK_THRESHOLD


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


def _find_by_id(items: Collection[_Identifiable], item_id: str) -> _Identifiable:
    try:
        return next(item for item in items if item.id == item_id)
    except StopIteration:
        # TODO univention/dev/education/user-management#214
        #      Handle this situation properly (context dependent),
        #      e.g. log an error and return user toast
        raise KeyError(f"Item with id {item_id} not found")


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


# Literals, not derived from the role id: a computed msgid is invisible to extraction.
_ROLE_LABELS = {
    "student": N_("Student"),
    "teacher": N_("Teacher"),
    "staff": N_("Staff"),
    "school_admin": N_("School Admin"),
    "legal_guardian": N_("Legal Guardian"),
}


def _display_name(user: User) -> str:
    """A person's name for labels and dialogs, falling back to the username."""
    return f"{user.attributes.first_name} {user.attributes.last_name}".strip() or (
        user.attributes.username
    )


def role_key(role: str) -> str:
    """The bare role name of a ``<role>:<context>:<id>`` string (``student``)."""
    return role.split(":", 1)[0]


def _role_label(role: str, lang: str) -> str:
    """A translated label for a role; an unlisted one degrades to its title-cased key."""
    key = role_key(role)
    return _(_ROLE_LABELS.get(key, key.replace("_", " ").title()), lang=lang)


def _format_role(schools: list[School], role: str, lang: str) -> str:
    school = _find_by_id(schools, role.rsplit(":", 1)[1])
    return f"{_role_label(role, lang)} ({school.display_name})"


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
    sections: list[tuple[str, str, list[SchoolClass] | list[WorkGroup]]] = [
        (SCHOOL_CLASS_KIND, _("Classes", lang=lang), school_classes),
        (WORK_GROUP_KIND, _("Work Groups", lang=lang), work_groups),
    ]
    for kind, heading, items in sections:
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
        rows.append(
            Row(
                id=user.id,
                cells=cells,
                label=_display_name(user),
                selectable=Permission.write_password in permissions,
            )
        )
    return UserListView(columns=list_columns(lang), rows=rows)


def build_password_reset_confirmation(
    data: PasswordResetSelectionData, lang: str
) -> PasswordResetConfirmation:
    """Build the confirmation dialog's view model for a selection.

    Names every account up to ``PASSWORD_RESET_NAMED_LIMIT`` and tallies the roles,
    so the dialog can state the scope before it can be submitted.
    """
    # Deduped per user: one role in two schools counts once, two roles count twice.
    tallies = Counter(
        key
        for user in data.users
        for key in dict.fromkeys(role_key(role) for role in user.attributes.roles)
    )

    accounts: list[PasswordResetAccount] = []
    if len(data.users) <= PASSWORD_RESET_NAMED_LIMIT:
        accounts = [
            PasswordResetAccount(name=_display_name(user), username=user.attributes.username)
            for user in data.users
        ]
    return PasswordResetConfirmation(
        target_ids=[user.id for user in data.users],
        accounts=accounts,
        # Sorted so the mixed-roles warning names the dominant role first.
        role_tallies=sorted(
            (RoleTally(label=_role_label(role, lang), count=count) for role, count in tallies.items()),
            key=lambda tally: (-tally.count, tally.label),
        ),
        denied=data.denied,
        supports_change_on_next_login=data.supports_change_on_next_login,
    )


def build_password_reset_summary(data: PasswordResetResultData, lang: str) -> tuple[str, str]:
    """Summarize a bulk password reset as a single toast message + variant.

    Interim rendering only - the UI issue for this feature replaces this with a
    per-user result region once its confirmation-dialog dependency exists.
    """
    if data.request_error == PasswordResetRequestError.no_targets:
        return _("Select at least one user before resetting passwords.", lang=lang), "error"
    if data.request_error == PasswordResetRequestError.empty_password:
        return _("A new password is required.", lang=lang), "error"
    if data.request_error == PasswordResetRequestError.too_many_targets:
        return (
            _("Select at most {max_targets} users at once.", lang=lang).format(
                max_targets=PASSWORD_RESET_MAX_TARGETS
            ),
            "error",
        )
    succeeded = sum(
        1 for outcome in data.outcomes if outcome.outcome == PasswordResetOutcomeCode.success
    )
    total = len(data.outcomes)
    message = _("Password reset for {succeeded} of {total} users.", lang=lang).format(
        succeeded=succeeded, total=total
    )
    variant = "success" if succeeded == total else "error"
    return message, variant


def build_password_reset_outcome_rows(
    data: PasswordResetResultData, lang: str
) -> list[PasswordResetOutcomeRow]:
    """The failures of a bulk reset, one row each, with their reason.

    Failures only: the toast carries "reset N of M", and listing successes buries
    the rows that need acting on. Empty means everything succeeded.
    """
    labels = {
        PasswordResetOutcomeCode.permission_denied: _("Permission denied", lang=lang),
        PasswordResetOutcomeCode.not_found: _("User not found", lang=lang),
        PasswordResetOutcomeCode.rejected: _("Rejected", lang=lang),
        PasswordResetOutcomeCode.unconfirmed: _(
            "Could not be confirmed - the password may have been changed. "
            "Please check this account before retrying.",
            lang=lang,
        ),
        PasswordResetOutcomeCode.next_login_change_unsupported: _(
            "This account cannot be required to change its password at the next login, "
            "so the password was left unchanged.",
            lang=lang,
        ),
    }
    return [
        PasswordResetOutcomeRow(
            target_id=outcome.target_id, label=labels[outcome.outcome], reason=outcome.reason
        )
        for outcome in data.outcomes
        if outcome.outcome != PasswordResetOutcomeCode.success
    ]
