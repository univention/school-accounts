# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
from enum import StrEnum, auto
from typing import Any, Optional

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


class TargetObject(BaseModel):
    id: str
    type: TargetObjectType
    attributes: dict[str, Any]


class Target(BaseModel):
    old_target: Optional[TargetObject]
    new_target: Optional[TargetObject]


class Permission(StrEnum):
    create_user = "create-user"
    delete_user = "delete-user"
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
    write_last_name = "write-last_name"
    write_first_name = "write-first_name"
    write_username = "write-username"
    write_activated = "write-activated"
    write_schools = "write-schools"
    write_school_classes = "write-school_classes"
    write_work_groups = "write-work_groups"
    write_roles = "write-roles"
    write_password = "write-password"  # nosec B105
    write_email = "write-email"
    write_birthday = "write-birthday"
    write_expiration_date = "write-expiration_date"
