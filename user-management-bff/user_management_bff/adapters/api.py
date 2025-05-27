# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
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
    ListSchoolClass,
    ListSchoolClassesResponse,
    ListSchoolsResponse,
    ListUser,
    ListUserAttribute,
    ListUserFixedAttributes,
    ListUserPermissions,
    ListUsersConfig,
    ListUsersResponse,
    ListWorkGroup,
    ListWorkGroupsResponse,
    PageConfig,
    RoleRow,
    RoleRowAttributes,
    SchoolClassRow,
    SchoolClassRowAttributes,
    SchoolContextPermission,
    WidgetType,
    WorkGroupRow,
    WorkGroupRowAttributes,
)
from ..lang import _
from ..models import Permission, School, SchoolClass, User, WorkGroup
from ..ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
    ListConfigRepresentationPort,
    SchoolClassesRepresentationPort,
    SchoolsRepresentationPort,
    UsersRepresentationPort,
    WorkGroupsRepresentationPort,
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
    def _format_list_view_user_attributes(
        list_user_attributes: ListUserFixedAttributes,
        user: User,
        permissions: set[Permission],
        schools: list[School],
        school_classes: dict[str, list[SchoolClass]],
        work_groups: dict[str, list[WorkGroup]],
        lang: str,
    ) -> ListUserFixedAttributes:
        def _find_item_by_id(items: list[Any], item_id: str):
            item_ids = [item for item in items if item.id == item_id]
            if item_ids:
                return item_ids[0]

        def _ui_formatted_school(school_objects: list[School], school_id: str) -> str:
            return _find_item_by_id(school_objects, school_id).display_name

        def _ui_formatted_school_class(
            school_objects: list[School],
            school_class_objects: list[SchoolClass],
            school_id: str,
            school_class_id: str,
        ) -> str:
            school = _find_item_by_id(school_objects, school_id)
            school_class = _find_item_by_id(school_class_objects, school_class_id)
            return f"{school_class.display_name} ({school.display_name})"

        def _ui_formatted_work_groups(
            school_objects: list[School],
            work_group_objects: list[WorkGroup],
            school_id: str,
            work_group_id: str,
        ) -> str:
            school = _find_item_by_id(school_objects, school_id)
            work_group = _find_item_by_id(work_group_objects, work_group_id)
            return f"{work_group.display_name} ({school.display_name})"

        def _ui_formatted_role(school_objects: list[School], role: str) -> str:
            school_id = role.rsplit(":", 1)[1]
            school = _find_item_by_id(school_objects, school_id)
            role_str = role.replace("_", " ").split(":", 1)[0].title()
            return f"{_(role_str,lang=lang)} ({school.display_name})"

        list_user_attributes.classes = ListUserAttribute[list[str]](
            **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                "school_classes",
                [
                    _ui_formatted_school_class(
                        school_objects=schools,
                        school_class_objects=school_classes[school],
                        school_id=school,
                        school_class_id=school_class,
                    )
                    for school, sclasses in user.attributes.school_classes.items()
                    for school_class in sclasses
                ],
                permissions,
            )
        )

        list_user_attributes.work_groups = ListUserAttribute[list[str]](
            **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                "work_groups",
                [
                    _ui_formatted_work_groups(
                        school_objects=schools,
                        work_group_objects=work_groups[school],
                        school_id=school,
                        work_group_id=work_group,
                    )
                    for school, wgroups in user.attributes.work_groups.items()
                    for work_group in wgroups
                ],
                permissions,
            )
        )

        list_user_attributes.schools = ListUserAttribute[list[str]](
            **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                "schools",
                [
                    _ui_formatted_school(school_objects=schools, school_id=school)
                    for school in user.attributes.schools
                ],
                permissions,
            )
        )
        list_user_attributes.roles = ListUserAttribute[list[str]](
            **FastAPIUsersRepresentationAdapter._get_attribute_dict(
                "roles",
                [
                    _ui_formatted_role(
                        school_objects=schools,
                        role=role,
                    )
                    for role in user.attributes.roles
                ],
                permissions,
            )
        )

        return list_user_attributes

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

    def create_users_representation(
        self,
        users: list[User],
        schools: list[School],
        school_classes: dict[str, list[SchoolClass]],
        work_groups: dict[str, list[WorkGroup]],
        permissions: dict[str, list[Permission]],
        lang: str,
    ) -> ListUsersResponse:
        list_users = []
        for user in users:
            # If the user has no permissions for the user,
            # we ignore them.
            # The `read_username` permission is currently implicit,
            # so we cannot have a situation where an actor can see a target user
            # with only `read_username` permissions.
            user_permissions = permissions.get(user.id, [])
            if user_permissions := permissions.get(user.id, []):
                list_user = ListUser(
                    id=user.id,
                    allowed_actions=(
                        [ListUserPermissions.DELETE]
                        if Permission.delete_user in user_permissions
                        else []
                    ),
                    attributes=self._get_list_user_attributes_from_user(user, set(user_permissions)),
                )

                list_user.attributes = self._format_list_view_user_attributes(
                    list_user_attributes=list_user.attributes,
                    user=user,
                    permissions=set(user_permissions),
                    schools=schools,
                    school_classes=school_classes,
                    work_groups=work_groups,
                    lang=lang,
                )
                list_users.append(list_user)

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


class FastAPISchoolClassesRepresentationAdapter(
    SchoolClassesRepresentationPort[ListSchoolClassesResponse]
):
    def create_school_classes_representation(
        self, school_classes: list[SchoolClass]
    ) -> ListSchoolClassesResponse:
        sorted_school_classes = sorted(school_classes, key=lambda x: x.display_name)
        list_school_classes = [
            ListSchoolClass(label=school_class.display_name, value=school_class.id)
            for school_class in sorted_school_classes
        ]
        return ListSchoolClassesResponse(school_classes=list_school_classes)


class FastAPIWorkGroupsRepresentationAdapter(WorkGroupsRepresentationPort[ListWorkGroupsResponse]):
    def create_work_groups_representation(self, work_groups: list[WorkGroup]) -> ListWorkGroupsResponse:
        sorted_work_groups = sorted(work_groups, key=lambda x: x.display_name)
        list_work_groups = [
            ListWorkGroup(label=work_group.display_name, value=work_group.id)
            for work_group in sorted_work_groups
        ]
        return ListWorkGroupsResponse(work_groups=list_work_groups)


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
                    label=_("Work Groups", lang=lang),
                    attribute="work_groups",
                    formatter=Formatter(
                        type=FormatterChoice.LIST,
                    ),
                    order=5,
                ),
                ColumnConfig(
                    label=_("Schools", lang=lang),
                    attribute="schools",
                    formatter=Formatter(
                        type=FormatterChoice.LIST,
                    ),
                    order=6,
                ),
                ColumnConfig(
                    label=_("Activated", lang=lang),
                    attribute="activated",
                    formatter=Formatter(
                        type=FormatterChoice.BOOLEAN,
                    ),
                    order=7,
                ),
            ],
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
