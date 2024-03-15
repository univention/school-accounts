# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum, auto
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

from .models import Role


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


class SchoolContextPermission(StrEnum):
    ADD = auto()


class Formatter(BaseModel):
    type: FormatterChoice


class LabeledValue(BaseModel):
    label: str
    value: str


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
    permissions: list[SchoolContextPermission]


class ListSchoolsResponse(BaseModel):
    schools: list[ListSchool]


class UserCreateRequest(BaseModel):
    last_name: str
    first_name: str
    username: str | None = None
    password: str | None = None
    schools: list[str]
    school_classes: dict[str, list[str]]
    roles: list[Role]
    disabled: bool = False

    @model_validator(mode="after")
    def check_schools(self) -> "UserCreateRequest":
        for school, classes in self.school_classes.items():
            if school not in self.schools:
                raise ValueError(f"School '{school}' is not present in the user's schools list")
        return self

    @model_validator(mode="after")
    def check_school_classes_for_student(self) -> "UserCreateRequest":
        if Role.STUDENT in self.roles and not self.school_classes:
            raise ValueError(
                "At least one school class for each school must be present when the user is a student"
            )
        return self


class CreateUserResponseUser(BaseModel):
    id: str
    attributes: ListUserFixedAttributes


class CreateUserResponse(BaseModel):
    user: CreateUserResponseUser


class Watcher(BaseModel):
    fields: list[str]
    callback_url: str


class WidgetType(StrEnum):
    UInputText = "UInputText"
    UInputPassword = "UInputPassword"
    USelect = "USelect"
    UMultiSelect = "UMultiSelect"
    UInputCheckbox = "UInputCheckbox"


class Fieldset(BaseModel):
    type: WidgetType
    props: dict[str, Any]
    watches: list[Watcher] = Field(default_factory=list)


class PageConfig(BaseModel):
    label: str
    name: str
    fieldsets: list[Fieldset]


class AddUsersConfig(BaseModel):
    pages: list[PageConfig]


class EditUsersConfig(BaseModel):
    id: str
    user: dict[str, Any]
    pages: list[PageConfig]


class SchoolCLassRowAttributes(BaseModel):
    class_name: LabeledValue


class SchoolClassRow(BaseModel):
    id: str
    attributes: SchoolCLassRowAttributes


class SchoolClassesConfig(BaseModel):
    rows: list[SchoolClassRow]
