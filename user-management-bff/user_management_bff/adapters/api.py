# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
from typing import Any

from ..api_models import (
    AddUsersConfig,
    ColumnConfig,
    CompleteUserFixedAttributes,
    CreateUserResponse,
    CreateUserResponseUser,
    EditUserResponseUser,
    EditUsersConfig,
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
    EditConfigRepresentationPort,
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

    @staticmethod
    def _get_edit_user_attributes_from_user(
        user: User, permissions: set[Permission]
    ) -> CompleteUserFixedAttributes:
        list_user_attributes = FastAPIUsersRepresentationAdapter._get_list_user_attributes_from_user(
            user, permissions
        )
        return CompleteUserFixedAttributes(
            **list_user_attributes.model_dump(),
            password=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "password", user.attributes.password, permissions
                )
            ),
            email=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "email", user.attributes.email, permissions
                )
            ),
            birthday=ListUserAttribute[datetime.date](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "birthday", user.attributes.birthday, permissions
                )
            ),
            expiration_date=ListUserAttribute[datetime.date](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "expiration_date", user.attributes.expiration_date, permissions
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

    def edit_user_representation(self, user: User, permissions: set[Permission]) -> EditUserResponseUser:
        return EditUserResponseUser(
            id=user.id,
            attributes=self._get_edit_user_attributes_from_user(user, permissions),
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


class FastAPIEditConfigRepresentationAdapter(
    EditConfigRepresentationPort[EditUsersConfig, EditUserResponseUser]
):
    def edit_config_representation(
        self,
        user_data: EditUserResponseUser,
        school: School,
        school_classes: list[SchoolClass],
        work_groups: list[WorkGroup],
        lang: str,
    ) -> EditUsersConfig:
        user = {key: value.value for key, value in dict(user_data.attributes).items()}
        user["school"] = school.id
        del user["schools"]
        user["school_classes"] = [
            c.split(":")[1] for c in user["classes"] if c.split(":")[0] == school.id
        ]
        del user["classes"]
        user["roles"] = [role.split(":")[0] for role in user["roles"] if role.split(":")[2] == school.id]

        return EditUsersConfig(
            # Be sure to send complete data,
            # otherwise it confuses the frontend,
            # unless the AttributeAccess is NONE,
            # in which case don't send it or send None.
            # user=dict(user_data.attributes),
            # user from the user attributes dict with the key value
            user=user,
            id=user_data.id,
            pages=[
                PageConfig(
                    label=_("User detail", lang=lang),
                    name="useredit",
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
                                            {"label": school.display_name, "value": school.id},
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
                                            access=user_data.attributes.last_name.access,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label=_("First name", lang=lang),
                                            name="first_name",
                                            description=_("First name of the user", lang=lang),
                                            required=True,
                                            access=user_data.attributes.first_name.access,
                                        ),
                                    ),
                                ],
                                [
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label=_("Username", lang=lang),
                                            name="username",
                                            description=_("Username of the user", lang=lang),
                                            required=False,
                                            access=user_data.attributes.username.access,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label=_("Email", lang=lang),
                                            name="email",
                                            description=_("Email of the user", lang=lang),
                                            required=False,
                                            access=user_data.attributes.email.access,
                                        ),
                                    ),
                                ],
                                # The frontend can technically handle this,
                                # and we'll keep it here for now.
                                # But you might want to consider just omitting NONE fields,
                                # so the user isn't aware of what they shouldn't know about.
                                # It also makes for a better Detail view,
                                # when it's not cluttered with disabled fields.
                                FieldsetRow(
                                    type=WidgetType.UInputPassword,
                                    props=dict(
                                        label=_("Password", lang=lang),
                                        name="password",
                                        description=_("Password of the user", lang=lang),
                                        required=False,
                                        access=user_data.attributes.password.access,
                                    ),
                                ),
                                [
                                    FieldsetRow(
                                        type=WidgetType.UInputDate,
                                        props=dict(
                                            label=_("Birthday", lang=lang),
                                            name="birthday",
                                            description=_("Birthday of the user", lang=lang),
                                            required=False,
                                            access=user_data.attributes.birthday.access,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputDate,
                                        props=dict(
                                            label=_("Expiration date", lang=lang),
                                            name="expiration_date",
                                            description=_("Expiration date of the user", lang=lang),
                                            required=False,
                                            access=user_data.attributes.expiration_date.access,
                                        ),
                                    ),
                                ],
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label=_("School classes", lang=lang),
                                        name="school_classes",
                                        description=_("School classes of the user", lang=lang),
                                        required=False,
                                        access=user_data.attributes.classes.access,
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
                                        access=user_data.attributes.roles.access,
                                        columns=[
                                            ColumnConfig(
                                                label=_("Role", lang=lang),
                                                attribute="role_name",
                                                order=0,
                                            )
                                        ],
                                        # We need to include all roles here
                                        # in order for it to display properly.
                                        # If you don't want to show certain roles,
                                        # set AttributeAccess.NONE
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
                                            RoleRow(
                                                id="staff",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value=_("Staff", lang=lang),
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="school_admin",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value=_("School Admin", lang=lang),
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
                                        access=user_data.attributes.activated.access,
                                    ),
                                ),
                            ],
                        )
                    ],
                )
            ],
        )
