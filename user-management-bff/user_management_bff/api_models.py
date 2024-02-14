# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum, auto
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


class SortingChoice(StrEnum):
    ASC = auto()
    DESC = auto()


class FormatterChoice(StrEnum):
    LIST = auto()
    BOOLEAN = auto()


class AttributeAccess(StrEnum):
    READ = auto()
    WRITE = auto()
    NONE = auto()


class Formatter(BaseModel):
    type: FormatterChoice


class ColumnConfig(BaseModel):
    label: str
    attribute: str
    order: int
    sorting: Optional[SortingChoice] = None
    formatter: Optional[Formatter] = None


class ListUsersConfig(BaseModel):
    columns: list[ColumnConfig]


AttributeType = TypeVar("AttributeType")


class ListUserAttribute(BaseModel, Generic[AttributeType]):
    value: Optional[AttributeType] = None
    access: AttributeAccess = AttributeAccess.NONE


class ListUserFixedAttributes(BaseModel):
    """
    For now the attributes the API exposes are fixed and not configurable.

    If this changes in the future, this class will have to be changed or replaced
    by the dynamic representation.
    """

    last_name: ListUserAttribute[str]
    first_name: ListUserAttribute[str]
    username: ListUserAttribute[str]
    activated: ListUserAttribute[bool]
    schools: ListUserAttribute[list[str]]
    classes: ListUserAttribute[list[str]]
    roles: ListUserAttribute[list[str]]


class ListUser(BaseModel):
    id: str
    attributes: ListUserFixedAttributes


class ListUsersResponse(BaseModel):
    users: list[ListUser]


class ListSchool(BaseModel):
    label: str
    value: str


class ListSchoolsResponse(BaseModel):
    schools: list[ListSchool]
