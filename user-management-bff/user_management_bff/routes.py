# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from . import business_logic
from .adapter_registry import port_dep
from .adapters.api import FastAPISchoolsRepresentationAdapter, FastAPIUsersRepresentationAdapter
from .api_models import (
    AddUsersConfig,
    APIUserPatchRequest,
    Attribute,
    AttributeAccess,
    ColumnConfig,
    CreateUserResponse,
    EditUsersConfig,
    Fieldset,
    FieldsetRow,
    FormatterChoice,
    ListSchoolsResponse,
    ListUsersConfig,
    ListUsersResponse,
    PageConfig,
    RoleRow,
    RoleRowAttributes,
    SchoolClassRow,
    SchoolCLassRowAttributes,
    UserCreateRequest,
    WidgetType,
)
from .constants import API_PREFIX
from .errors import CreationError
from .models import UserPatchAttributes, UserPatchRequest, UsersGetRequest
from .ports import (
    FastAPIAuthenticationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UsersPersistencePort,
    UsersRepresentationPort,
)

router = APIRouter(prefix=API_PREFIX)

COLUMN_CONFIGS: list[dict[str, Any]] = [
    {
        "label": "Last name",
        "attribute": "last_name",
        "sorting": "asc",
    },
    {
        "label": "First name",
        "attribute": "first_name",
        "sorting": "asc",
    },
    {
        "label": "Username",
        "attribute": "username",
    },
    {
        "label": "Roles",
        "attribute": "roles",
        "formatter": {"type": FormatterChoice.LIST},
    },
    {
        "label": "Classes",
        "attribute": "classes",
        "formatter": {"type": FormatterChoice.LIST},
    },
    {
        "label": "Schools",
        "attribute": "schools",
        "formatter": {"type": FormatterChoice.LIST},
    },
    {
        "label": "Active",
        "attribute": "active",
        "formatter": {"type": FormatterChoice.BOOLEAN},
    },
]


@router.get("/config/users/list")
def get_users_config() -> ListUsersConfig:
    return ListUsersConfig(
        columns=[ColumnConfig(**column, order=index) for index, column in enumerate(COLUMN_CONFIGS)]
    )


@router.get("/users")
async def get_users(
    request: Request,
    school: str,
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> ListUsersResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.get_users(
        users_get_adapter,
        representation_adapter,
        permissions_port,
        actor_id,
        UsersGetRequest(school=school),
    )


@router.get("/config/schools")
async def get_schools(
    request: Request,
    schools_get_adapter: SchoolsPersistencePort = Depends(port_dep(SchoolsPersistencePort)),
    representation_adapter: FastAPISchoolsRepresentationAdapter = Depends(
        port_dep(SchoolsRepresentationPort, adapter_cls=FastAPISchoolsRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
) -> ListSchoolsResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.get_schools(
        schools_get_adapter, representation_adapter, permissions_port, users_get_adapter, actor_id
    )


@router.post("/users", status_code=201)
async def create_user(
    request: Request,
    user: UserCreateRequest,
    users_post_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> CreateUserResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    try:
        return await business_logic.create_user(
            users_post_adapter,
            representation_adapter,
            users_get_adapter,
            permissions_port,
            actor_id,
            user,
        )
    except CreationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Currently a mock. Response model should be renamed with proper implementation
@router.patch("/users/{id}")
async def patch_user(
    request: Request,
    user_id: Annotated[str, Path(alias="id")],
    school: str,
    user_patch_data: APIUserPatchRequest,
    users_patch_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> CreateUserResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    patch_data = UserPatchRequest(
        identifier=user_id,
        school=school,
        attributes=UserPatchAttributes(**user_patch_data.model_dump(exclude_unset=True)),
    )
    return await business_logic.patch_user(
        users_patch_adapter, representation_adapter, permissions_port, actor_id, patch_data
    )


@router.get("/config/users/add")
async def get_user_add_config(
    request: Request,
    school: str,
    school_classes_persistence_port: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> AddUsersConfig:
    actor_id = await authentication_port.get_authenticated_id(request)
    school_classes = await business_logic.get_user_add_config_data(
        school_classes_persistence_port, permissions_port, actor_id, school
    )
    # TODO: get school data, and put in 'school' FieldsetRow
    schoolobj = {
        "id": school,
        "name": school.title(),
    }
    # TODO: Construction of a response really belongs in business logic, not here.
    # Routers should be relatively sparse, and this makes the router bloated.
    # Putting the response creation in business logic allows for better unit tests,
    # especially if we need to add conditional logic later.
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
                                        {"label": schoolobj["name"], "value": schoolobj["id"]},
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
                                            attributes=SchoolCLassRowAttributes(
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
                                    columns=[ColumnConfig(label="Role", attribute="role_name", order=0)],
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


# currently a mock
@router.get("/config/users/edit")
def get_user_edit_config(
    user_id: Annotated[str, Query(alias="id")], school: str
) -> EditUsersConfig:  # pragma: no cover
    # TODO: get school data, and put in 'school' FieldsetRow
    schoolobj = {
        "id": school,
        "name": school.title(),
    }
    return EditUsersConfig(
        id="user1",
        # Be sure to send complete data,
        # otherwise it confuses the frontend,
        # unless the AttributeAccess is NONE,
        # in which case don't send it or send None.
        user={
            "username": "user1",  # username should match id
            "first_name": "Max",
            "last_name": "Mustermann",
            "school": school,
            "school_classes": ["school_class1"],
            "roles": ["student"],
            "active": True,
        },
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
                                        {"label": schoolobj["name"], "value": schoolobj["id"]},
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
                                    required=False,
                                    access=AttributeAccess.WRITE,
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
                                    access=AttributeAccess.NONE,
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
                                            label="school class", attribute="class_name", order=0
                                        )
                                    ],
                                    rows=[
                                        SchoolClassRow(
                                            id="school_class1",
                                            attributes=SchoolCLassRowAttributes(
                                                class_name=Attribute(
                                                    value="Class 1", access=AttributeAccess.READ
                                                )
                                            ),
                                        ),
                                        SchoolClassRow(
                                            id="school_class2",
                                            attributes=SchoolCLassRowAttributes(
                                                class_name=Attribute(
                                                    value="Class 2", access=AttributeAccess.READ
                                                )
                                            ),
                                        ),
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
                                    access=AttributeAccess.READ,
                                    columns=[ColumnConfig(label="Role", attribute="role_name", order=0)],
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
                                    access=AttributeAccess.READ,
                                ),
                            ),
                        ],
                    )
                ],
            )
        ],
    )


@router.delete("/users/{identifier}", status_code=204)
async def delete_user(
    request: Request,
    identifier: str,
    users_delete_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> None:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.delete_user(users_delete_adapter, permissions_port, actor_id, identifier)
