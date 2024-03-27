# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum, auto
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from .models import Role


class APIBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


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


class Attribute(BaseModel):
    value: str
    access: AttributeAccess


class SchoolContextPermission(StrEnum):
    ADD = auto()


class ListUserPermissions(StrEnum):
    DELETE = auto()


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
    active: ListUserAttribute[bool]
    schools: ListUserAttribute[list[str]]
    classes: ListUserAttribute[list[str]]
    roles: ListUserAttribute[list[str]]


class CompleteUserFixedAttributes(ListUserFixedAttributes):
    password: ListUserAttribute[str]


class ListUser(APIBaseModel):
    id: str
    allowed_actions: list[ListUserPermissions]
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
    school: str
    school_classes: list[str]
    roles: list[str]
    active: bool = True

    @model_validator(mode="after")
    def check_school_classes_for_student(self) -> "UserCreateRequest":
        if Role.STUDENT in self.roles and len(self.school_classes) == 0:
            raise ValueError("A student must have at least one school class.")
        return self


class APIUserPatchRequest(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    username: Optional[str] = None
    password: str | None = None
    school_classes: Optional[list[str]] = None
    active: Optional[bool] = None
    roles: Optional[list[str]] = None


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
    UComboBox = "UComboBox"
    UMultiSelect = "UMultiSelect"
    UInputCheckbox = "UInputCheckbox"


class FieldsetRow(BaseModel):
    type: WidgetType
    props: dict[str, Any]
    watches: list[Watcher] = Field(default_factory=list)


class Fieldset(BaseModel):
    name: str
    label: str
    rows: list[FieldsetRow | list[FieldsetRow]]


class PageConfig(BaseModel):
    label: str
    name: str
    fieldsets: list[Fieldset]


class AddUsersConfig(BaseModel):
    pages: list[PageConfig]


class EditUserResponseUser(BaseModel):
    id: str
    attributes: CompleteUserFixedAttributes


class EditUsersConfig(BaseModel):
    id: str
    user: dict[str, Any]
    pages: list[PageConfig]


class RoleRowAttributes(BaseModel):
    role_name: Attribute


class RoleRow(BaseModel):
    id: str
    attributes: RoleRowAttributes


class SchoolClassRowAttributes(BaseModel):
    class_name: Attribute


class SchoolClassRow(BaseModel):
    id: str
    attributes: SchoolClassRowAttributes
