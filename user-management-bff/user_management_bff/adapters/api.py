# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Any

from ..api_models import (
    AddUsersConfig,
    Attribute,
    AttributeAccess,
    ColumnConfig,
    CompleteUserFixedAttributes,
    CreateUserResponse,
    CreateUserResponseUser,
    EditUserResponseUser,
    EditUsersConfig,
    Fieldset,
    FieldsetRow,
    Formatter,
    FormatterChoice,
    LabeledValue,
    ListSchool,
    ListSchoolsResponse,
    ListUser,
    ListUserAttribute,
    ListUserFixedAttributes,
    ListUserPermissions,
    ListUsersConfig,
    ListUsersResponse,
    PageConfig,
    RoleRow,
    RoleRowAttributes,
    SchoolClassRow,
    SchoolClassRowAttributes,
    SchoolContextPermission,
    WidgetType,
)
from ..lang import _
from ..models import Permission, School, SchoolClass, User
from ..ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
    ListConfigRepresentationPort,
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

    @staticmethod
    def _get_edit_user_attributes_from_user(
        user: User, permissions: set[Permission]
    ) -> CompleteUserFixedAttributes:
        list_user_atributes = FastAPIUsersRepresentationAdapter._get_list_user_attributes_from_user(
            user, permissions
        )
        return CompleteUserFixedAttributes(
            **list_user_atributes.model_dump(),
            password=ListUserAttribute[str](
                **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                    "password", user.attributes.password, permissions
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
            attributes=self._get_edit_user_attributes_from_user(user, permissions),
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


class FastAPIListConfigRepresentationAdapter(ListConfigRepresentationPort[ListUsersConfig]):
    def list_config_representation(self, lang: str = "en"):
        return ListUsersConfig(
            columns=[
                ColumnConfig(
                    label=_("Last name", lang=lang),
                    attribute="last_name",
                    sorting="asc",
                    order=0,
                ),
                ColumnConfig(
                    label=_("First name", lang=lang),
                    attribute="first_name",
                    sorting="asc",
                    order=1,
                ),
                ColumnConfig(
                    label=_("Username", lang=lang),
                    attribute="username",
                    order=2,
                ),
                ColumnConfig(
                    label=_("Roles", lang=lang),
                    attribute="roles",
                    formatter=Formatter(
                        type=FormatterChoice.LIST,
                    ),
                    order=3,
                ),
                ColumnConfig(
                    label=_("Classes", lang=lang),
                    attribute="classes",
                    formatter=Formatter(
                        type=FormatterChoice.LIST,
                    ),
                    order=4,
                ),
                ColumnConfig(
                    label=_("Schools", lang=lang),
                    attribute="schools",
                    formatter=Formatter(
                        type=FormatterChoice.LIST,
                    ),
                    order=5,
                ),
                ColumnConfig(
                    label=_("Active", lang=lang),
                    attribute="active",
                    formatter=Formatter(
                        type=FormatterChoice.BOOLEAN,
                    ),
                    order=6,
                ),
            ],
        )


class FastAPIAddConfigRepresentationAdapter(AddConfigRepresentationPort[AddUsersConfig]):
    def add_config_representation(
        self, school: School, school_classes: list[SchoolClass], lang: str
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
                                        label=_("Active", lang=lang),
                                        name="active",
                                        description=_("User is active", lang=lang),
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
                                                id="administrator",
                                                attributes=RoleRowAttributes(
                                                    role_name=Attribute(
                                                        value=_("Administrator", lang=lang),
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
                                        label=_("Active", lang=lang),
                                        name="active",
                                        description=_("User is active", lang=lang),
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
