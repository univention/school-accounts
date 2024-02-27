# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from enum import StrEnum, auto
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

AttributeType = TypeVar("AttributeType")


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
    roles: list[str]


class User(BaseModel):
    id: str
    attributes: UserAttributes


class School(BaseModel):
    id: str
    display_name: str


class UsersGetRequest(BaseModel):
    school: str


class TargetObjectType(StrEnum):
    SCHOOL = auto()


class TargetObject(BaseModel):
    id: str
    type: TargetObjectType
    attributes: dict[str, Any]


class Target(BaseModel):
    old_target: Optional[TargetObject]
    new_target: Optional[TargetObject]


class Permission(StrEnum):
    create_user = "create-user"
