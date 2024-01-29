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
    STRING = auto()
    LIST = auto()


class ColumnConfig(BaseModel):
    label: str
    attribute: str
    order: int
    sorting: SortingChoice = SortingChoice.ASC
    formatter: FormatterChoice = FormatterChoice.STRING


class ListUsersConfig(BaseModel):
    columns: list[ColumnConfig]


AttributeType = TypeVar("AttributeType")


class ListUserAttribute(BaseModel, Generic[AttributeType]):
    value: Optional[AttributeType] = None
    visible: bool = False


class ListUserFixedAttributes(BaseModel):
    """
    For now the attributes the API exposes are fixed and not configurable.

    If this changes in the future, this class will have to be changed or replaced
    by the dynamic representation.
    """

    last_name: ListUserAttribute[str]
    first_name: ListUserAttribute[str]
    username: ListUserAttribute[str]
    disabled: ListUserAttribute[bool]
    schools: ListUserAttribute[list[str]]
    roles: ListUserAttribute[list[str]]


class ListUser(BaseModel):
    id: str
    attributes: ListUserFixedAttributes


class ListUsersResponse(BaseModel):
    users: list[ListUser]
