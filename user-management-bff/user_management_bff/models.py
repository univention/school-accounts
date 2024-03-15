# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from enum import StrEnum, auto
from typing import Any, Optional, TypeVar

from pydantic import BaseModel, model_validator

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
    password: str | None = None


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


class Role(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"


class UserCreateRequest(BaseModel):
    last_name: str
    first_name: str
    username: str | None = None
    password: str | None = None
    school: str
    school_classes: list[str]
    roles: list[Role]
    disabled: bool = False

    @model_validator(mode="after")
    def check_school_classes_for_student(self) -> "UserCreateRequest":
        if Role.STUDENT in self.roles and not self.school_classes:
            raise ValueError("A student must have at least one school class.")
        return self
