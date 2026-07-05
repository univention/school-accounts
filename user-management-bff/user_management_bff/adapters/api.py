# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Any

from ..api_models import (
    AddUsersConfig,
    ColumnConfig,
    CreateUserResponse,
    CreateUserResponseUser,
    Fieldset,
    FieldsetRow,
    LabeledValue,
    ListUserAttribute,
    ListUserFixedAttributes,
    PageConfig,
    RoleRow,
    RoleRowAttributes,
    SchoolClassRow,
    SchoolClassRowAttributes,
    WidgetType,
    WorkGroupRow,
    WorkGroupRowAttributes,
)
from ..lang import _
from ..models import Attribute, AttributeAccess, Permission, School, SchoolClass, User, WorkGroup
from ..ports import (
    AddConfigRepresentationPort,
    UsersRepresentationPort,
)


class FastAPIUsersRepresentationAdapter(UsersRepresentationPort[CreateUserResponse, CreateUserResponse]):
    @staticmethod
    def _get_attribute_dict(
        attribute_name: str, value: Any, permissions: set[Permission]
    ) -> dict[str, Any]:
        result = {"value": None, "access": AttributeAccess.NONE}
        if attribute_name == "username":  # username is always readable
            result["access"] = AttributeAccess.READ
            result["value"] = value
        try:
            if Permission(f"read-{attribute_name}") in permissions:
                result["access"] = AttributeAccess.READ
                result["value"] = value
        except ValueError:
            pass
        try:
            if Permission(f"write-{attribute_name}") in permissions:
                result["access"] = AttributeAccess.WRITE
                result["value"] = value
        except ValueError:
            pass
        return result

    @staticmethod
    def _get_list_user_attributes_from_user(
        user: User, permissions: set[Permission]
    ) -> ListUserFixedAttributes:
        return ListUserFixedAttributes(
            username=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "username", user.attributes.username, permissions
                )
            ),
            last_name=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "last_name", user.attributes.last_name, permissions
                )
            ),
            first_name=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "first_name", user.attributes.first_name, permissions
                )
            ),
            activated=ListUserAttribute[bool](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "activated", not user.attributes.disabled, permissions
                )
            ),
            classes=ListUserAttribute[list[str]](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "school_classes",
                    [
                        f"{school}:{school_class}"
                        for school, school_classes in user.attributes.school_classes.items()
                        for school_class in school_classes
                    ],
                    permissions,
                )
            ),
            work_groups=ListUserAttribute[list[str]](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "work_groups",
                    [
                        f"{school}:{work_group}"
                        for school, wgroups in user.attributes.work_groups.items()
                        for work_group in wgroups
                    ],
                    permissions,
                )
            ),
            schools=ListUserAttribute[list[str]](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "schools", [school for school in user.attributes.schools], permissions
                )
            ),
            roles=ListUserAttribute[list[str]](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "roles", [role for role in user.attributes.roles], permissions
                )
            ),
        )

    def create_user_representation(self, user: User, permissions: set[Permission]) -> CreateUserResponse:
        return CreateUserResponse(
            user=CreateUserResponseUser(
                id=user.id,
                attributes=self._get_list_user_attributes_from_user(user, permissions),
            )
        )


class FastAPIAddConfigRepresentationAdapter(AddConfigRepresentationPort[AddUsersConfig]):
    def add_config_representation(
        self, school: School, school_classes: list[SchoolClass], work_groups: list[WorkGroup], lang: str
    ) -> AddUsersConfig:
        return AddUsersConfig(
            pages=[
                PageConfig(
                    label=_("Add user", lang=lang),
                    name="useradd",
                    fieldsets=[
                        Fieldset(
                            name="userinfo",
                            label=_("User info", lang=lang),
                            rows=[
                                FieldsetRow(
                                    type=WidgetType.UComboBox,
                                    props=dict(
                                        label=_("School", lang=lang),
                                        name="school",
                                        description=_("School of the user", lang=lang),
                                        required=True,
                                        access=AttributeAccess.READ,
                                        options=[
                                            LabeledValue(
                                                label=school.display_name,
                                                value=school.id,
                                            ),
                                        ],
                                    ),
                                ),
                                [
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label=_("Last name", lang=lang),
                                            name="last_name",
                                            description=_("Last name of the user", lang=lang),
                                            required=True,
                                            access=AttributeAccess.WRITE,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label=_("First name", lang=lang),
                                            name="first_name",
                                            description=_("First name of the user", lang=lang),
                                            required=True,
                                            access=AttributeAccess.WRITE,
                                        ),
                                    ),
                                ],
                                FieldsetRow(
                                    type=WidgetType.UInputText,
                                    props=dict(
                                        label=_("Username", lang=lang),
                                        name="username",
                                        description=_("Username of the user", lang=lang),
                                        required=True,
                                        access=AttributeAccess.WRITE,
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UInputPassword,
                                    props=dict(
                                        label=_("Password", lang=lang),
                                        name="password",
                                        description=_("Password of the user", lang=lang),
                                        required=False,
                                        access=AttributeAccess.WRITE,
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label=_("School classes", lang=lang),
                                        name="school_classes",
                                        description=_("School classes of the user", lang=lang),
                                        required=False,
                                        access=AttributeAccess.WRITE,
                                        columns=[
                                            ColumnConfig(
                                                label=_("School class", lang=lang),
                                                attribute="class_name",
                                                order=0,
                                            )
                                        ],
                                        rows=[
                                            SchoolClassRow(
                                                id=school_class.id,
                                                attributes=SchoolClassRowAttributes(
                                                    class_name=Attribute(
                                                        value=school_class.display_name,
                                                        access=AttributeAccess.READ,
                                                    )
                                                ),
                                            )
                                            for school_class in school_classes
                                        ],
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label=_("Work Groups", lang=lang),
                                        name="work_groups",
                                        description=_("Work groups of the user", lang=lang),
                                        required=False,
                                        access=AttributeAccess.WRITE,
                                        columns=[
                                            ColumnConfig(
                                                label=_("Work group", lang=lang),
                                                attribute="work_group_name",
                                                order=0,
                                            )
                                        ],
                                        rows=[
                                            WorkGroupRow(
                                                id=work_group.id,
                                                attributes=WorkGroupRowAttributes(
                                                    work_group_name=Attribute(
                                                        value=work_group.display_name,
                                                        access=AttributeAccess.READ,
                                                    )
                                                ),
                                            )
                                            for work_group in work_groups
                                        ],
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label=_("Roles", lang=lang),
                                        name="roles",
                                        description=_("Roles of the user", lang=lang),
                                        required=True,
                                        access=AttributeAccess.WRITE,
                                        columns=[
                                            ColumnConfig(
                                                label=_("Role", lang=lang),
                                                attribute="role_name",
                                                order=0,
                                            )
                                        ],
                                        rows=[
                                            RoleRow(
                                                id="student",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value=_("Student", lang=lang),
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="teacher",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value=_("Teacher", lang=lang),
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                        ],
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UInputCheckbox,
                                    props=dict(
                                        label=_("Activated", lang=lang),
                                        name="activated",
                                        description=_("User is activated", lang=lang),
                                        required=False,
                                        access=AttributeAccess.WRITE,
                                    ),
                                ),
                            ],
                        )
                    ],
                )
            ]
        )
