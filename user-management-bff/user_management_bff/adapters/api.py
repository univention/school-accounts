# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Any

from ..api_models import (
    AddUsersConfig,
    Attribute,
    AttributeAccess,
    ColumnConfig,
    CreateUserResponse,
    CreateUserResponseUser,
    EditUserResponseUser,
    EditUsersConfig,
    Fieldset,
    FieldsetRow,
    LabeledValue,
    ListSchool,
    ListSchoolsResponse,
    ListUser,
    ListUserAttribute,
    ListUserFixedAttributes,
    ListUserPermissions,
    ListUsersResponse,
    PageConfig,
    RoleRow,
    RoleRowAttributes,
    SchoolClassRow,
    SchoolClassRowAttributes,
    SchoolContextPermission,
    WidgetType,
)
from ..models import Permission, School, SchoolClass, User
from ..ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
    SchoolsRepresentationPort,
    UsersRepresentationPort,
)


class FastAPIUsersRepresentationAdapter(UsersRepresentationPort[ListUsersResponse, CreateUserResponse]):

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
            active=ListUserAttribute[bool](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "active", not user.attributes.disabled, permissions
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

    def create_users_representation(
        self, users: list[User], permissions: dict[str, list[Permission]]
    ) -> ListUsersResponse:
        list_users = [
            ListUser(
                id=user.id,
                allowed_actions=(
                    [ListUserPermissions.DELETE] if Permission.delete_user in user_permissions else []
                ),
                attributes=self._get_list_user_attributes_from_user(user, set(user_permissions)),
            )
            for user in users
            if (user_permissions := permissions.get(user.id, [])) is not None
        ]
        return ListUsersResponse(users=list_users)

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
            attributes=self._get_list_user_attributes_from_user(user, permissions),
        )


class FastAPISchoolsRepresentationAdapter(SchoolsRepresentationPort[ListSchoolsResponse]):
    def create_schools_representation(
        self, schools: list[School], permissions: dict[str, list[Permission]]
    ) -> ListSchoolsResponse:
        sorted_schools = sorted(schools, key=lambda x: x.display_name)
        list_schools = [
            ListSchool(
                label=school.display_name,
                value=school.id,
                permissions=(
                    [SchoolContextPermission.ADD]
                    if "create-user" in permissions.get(school.id, [])
                    else []
                ),
            )
            for school in sorted_schools
        ]
        return ListSchoolsResponse(schools=list_schools)


class FastAPIAddConfigRepresentationAdapter(AddConfigRepresentationPort[AddUsersConfig]):
    def add_config_representation(
        self, school: School, school_classes: list[SchoolClass]
    ) -> AddUsersConfig:
        return AddUsersConfig(
            pages=[
                PageConfig(
                    label="Add user",
                    name="useradd",
                    fieldsets=[
                        Fieldset(
                            name="userinfo",
                            label="User Info",
                            rows=[
                                FieldsetRow(
                                    type=WidgetType.UComboBox,
                                    props=dict(
                                        label="School",
                                        name="school",
                                        description="School of the user",
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
                                            label="Last name",
                                            name="last_name",
                                            description="Last name of the user",
                                            required=True,
                                            access=AttributeAccess.WRITE,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label="First name",
                                            name="first_name",
                                            description="First name of the user",
                                            required=True,
                                            access=AttributeAccess.WRITE,
                                        ),
                                    ),
                                ],
                                FieldsetRow(
                                    type=WidgetType.UInputText,
                                    props=dict(
                                        label="Username",
                                        name="username",
                                        description="Username of the user",
                                        required=True,
                                        access=AttributeAccess.WRITE,
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UInputPassword,
                                    props=dict(
                                        label="Password",
                                        name="password",
                                        description="Password of the user",
                                        required=False,
                                        access=AttributeAccess.WRITE,
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label="School classes",
                                        name="school_classes",
                                        description="School classes of the user",
                                        required=True,
                                        access=AttributeAccess.WRITE,
                                        columns=[
                                            ColumnConfig(
                                                label="School class", attribute="class_name", order=0
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
                                        label="Roles",
                                        name="roles",
                                        description="Roles of the user",
                                        required=True,
                                        access=AttributeAccess.WRITE,
                                        columns=[
                                            ColumnConfig(label="Role", attribute="role_name", order=0)
                                        ],
                                        rows=[
                                            RoleRow(
                                                id="student",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value="Student",
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="teacher",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value="Teacher",
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
                                        label="Active",
                                        name="active",
                                        description="Active",
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
                    label="Edit user",
                    name="useredit",
                    fieldsets=[
                        Fieldset(
                            name="userinfo",
                            label="User Info",
                            rows=[
                                FieldsetRow(
                                    type=WidgetType.UComboBox,
                                    props=dict(
                                        label="School",
                                        name="school",
                                        description="School of the user",
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
                                            label="Last name",
                                            name="last_name",
                                            description="Last name of the user",
                                            required=True,
                                            access=user_data.attributes.last_name.access,
                                        ),
                                    ),
                                    FieldsetRow(
                                        type=WidgetType.UInputText,
                                        props=dict(
                                            label="First name",
                                            name="first_name",
                                            description="First name of the user",
                                            required=True,
                                            access=user_data.attributes.first_name.access,
                                        ),
                                    ),
                                ],
                                FieldsetRow(
                                    type=WidgetType.UInputText,
                                    props=dict(
                                        label="Username",
                                        name="username",
                                        description="Username of the user",
                                        required=False,
                                        access=user_data.attributes.username.access,
                                    ),
                                ),
                                # The frontend can technically handle this,
                                # and we'll keep it here for now.
                                # But you might want to consider just omitting NONE fields,
                                # so the user isn't aware of what they shouldn't know about.
                                # It also makes for a better Detail view,
                                # when it's not cluttered with disabled fields.
                                FieldsetRow(
                                    type=WidgetType.UInputPassword,
                                    props=dict(
                                        label="Password",
                                        name="password",
                                        description="Password of the user",
                                        required=False,
                                        access=AttributeAccess.WRITE,  # TODO
                                    ),
                                ),
                                FieldsetRow(
                                    type=WidgetType.UMultiSelect,
                                    props=dict(
                                        label="School classes",
                                        name="school_classes",
                                        description="School classes of the user",
                                        required=False,
                                        access=user_data.attributes.classes.access,
                                        columns=[
                                            ColumnConfig(
                                                label="school class", attribute="class_name", order=0
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
                                        label="Roles",
                                        name="roles",
                                        description="Roles of the user",
                                        required=True,
                                        access=user_data.attributes.roles.access,
                                        columns=[
                                            ColumnConfig(label="Role", attribute="role_name", order=0)
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
                                                        value="Student",
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="teacher",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value="Teacher",
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="staff",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value="Staff",
                                                        access=AttributeAccess.READ,
                                                    ),
                                                ),
                                            ),
                                            RoleRow(
                                                id="administrator",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value="Administrator",
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
                                        label="Active",
                                        name="active",
                                        description="User is active",
                                        required=False,
                                        access=user_data.attributes.active.access,
                                    ),
                                ),
                            ],
                        )
                    ],
                )
            ],
        )
