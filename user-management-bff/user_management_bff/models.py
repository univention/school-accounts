# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
from enum import StrEnum, auto
from typing import TypeAlias

from pydantic import BaseModel


class AttributeAccess(StrEnum):
    READ = auto()
    WRITE = auto()
    NONE = auto()


class UserAttributes(BaseModel):
    """
    For now the attributes are fixed and not configurable.

    If this changes in the future, this class will have to be changed or replaced
    by the dynamic representation.
    """

    last_name: str
    first_name: str
    username: str
    disabled: bool
    schools: list[str]
    school_classes: dict[str, list[str]]
    work_groups: dict[str, list[str]]
    roles: list[str]
    legal_wards: list[str] = []
    legal_guardians: list[str] = []
    password: str | None = None
    email: str | None = None
    birthday: datetime.date | None = None
    expiration_date: datetime.date | None = None


class User(BaseModel):
    id: str
    attributes: UserAttributes


class SessionRecord(BaseModel):
    """A server-side authenticated session.

    Holds only what the UI needs: the actor identifier used for permission
    checks plus the data required for logout and silent token refresh. The
    user's access token is deliberately not stored - downstream calls use the
    service account and identify the actor by ``actor_id``.
    """

    actor_id: str
    sub: str
    kc_sid: str | None = None
    expires_at: datetime.datetime
    refresh_token: str | None = None
    id_token: str | None = None


class School(BaseModel):
    id: str
    display_name: str


class SchoolClass(BaseModel):
    id: str
    display_name: str
    school: str


class WorkGroup(SchoolClass):
    pass


class UsersGetRequest(BaseModel):
    school: str
    school_classes: list[str]
    work_groups: list[str]


class TargetObjectType(StrEnum):
    SCHOOL = auto()
    USER = auto()
    SCHOOL_CLASS = auto()
    WORK_GROUP = auto()

    @property
    def sensitive_attributes(self) -> frozenset[str]:
        return _SENSITIVE_ATTRIBUTES_BY_TYPE.get(self, frozenset())


# Attribute names that must never be forwarded to a third-party PDP (e.g. Cerbos) as
# authorization data, keyed by the TargetObjectType they can appear on.
_SENSITIVE_ATTRIBUTES_BY_TYPE: dict[TargetObjectType, frozenset[str]] = {
    TargetObjectType.USER: frozenset({"password"}),
}


TargetObjectAttributeValue: TypeAlias = (
    str | bool | int | list[str] | dict[str, list[str]] | datetime.date | None
)


class TargetObject(BaseModel):
    id: str
    type: TargetObjectType
    attributes: dict[str, TargetObjectAttributeValue]


class Target(BaseModel):
    old_target: TargetObject | None
    new_target: TargetObject | None


class Permission(StrEnum):
    use_as_filter = "use-as-filter"  # Target can be used as a filter by actor when searching for users
    read_last_name = "read-last_name"
    read_first_name = "read-first_name"
    read_disabled = "read-disabled"
    read_activated = "read-activated"
    read_schools = "read-schools"
    read_school_classes = "read-school_classes"
    read_work_groups = "read-work_groups"
    read_roles = "read-roles"
    read_email = "read-email"
    read_birthday = "read-birthday"
    read_expiration_date = "read-expiration_date"
    write_password = "write-password"  # nosec B105
