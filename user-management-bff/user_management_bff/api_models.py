# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
from enum import StrEnum, auto
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from .lang import _
from .models import Attribute, AttributeAccess, Role


class APIBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SortingChoice(StrEnum):
    ASC = auto()
    DESC = auto()


class FormatterChoice(StrEnum):
    LIST = auto()
    BOOLEAN = auto()


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
    work_groups: ListUserAttribute[list[str]]
    roles: ListUserAttribute[list[str]]


class CompleteUserFixedAttributes(ListUserFixedAttributes):
    password: ListUserAttribute[str]
    email: ListUserAttribute[str]
    birthday: ListUserAttribute[datetime.date]
    expiration_date: ListUserAttribute[datetime.date]


class SchoolClassesGetRequest(BaseModel):
    school: str


class UserCreateRequest(BaseModel):
    last_name: str
    first_name: str
    username: str | None = None
    password: str | None = None
    school: str
    school_classes: list[str]
    roles: list[str]
    activated: bool = True
    work_groups: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_school_classes_for_student(self) -> "UserCreateRequest":
        if Role.STUDENT in self.roles and len(self.school_classes) == 0:
            raise ValueError(_("A student must be member of at least one school class."))
        return self


class APIUserPatchRequest(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    username: Optional[str] = None
    password: str | None = None
    school_classes: Optional[list[str]] = None
    activated: Optional[bool] = None
    roles: Optional[list[str]] = None
    email: Optional[str] = None
    birthday: Optional[datetime.date] = None
    expiration_date: Optional[datetime.date] = None


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
    UInputDate = "UInputDate"


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


class WorkGroupRowAttributes(BaseModel):
    work_group_name: Attribute


class SchoolClassRow(BaseModel):
    id: str
    attributes: SchoolClassRowAttributes


class WorkGroupRow(BaseModel):
    id: str
    attributes: WorkGroupRowAttributes
