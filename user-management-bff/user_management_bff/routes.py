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
    AttributeAccess,
    ColumnConfig,
    CreateUserResponse,
    EditUsersConfig,
    Fieldset,
    FormatterChoice,
    LabeledValue,
    ListSchoolsResponse,
    ListUsersConfig,
    ListUsersResponse,
    PageConfig,
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
        "label": "Activated",
        "attribute": "activated",
        "formatter": {"type": FormatterChoice.BOOLEAN},
    },
]


@router.get("/config-users")
def get_users_config() -> ListUsersConfig:
    return ListUsersConfig(
        columns=[ColumnConfig(**column, order=index) for index, column in enumerate(COLUMN_CONFIGS)]
    )


@router.get("/users")
async def get_users(
    school: str,
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
) -> ListUsersResponse:
    return await business_logic.get_users(
        users_get_adapter, representation_adapter, UsersGetRequest(school=school)
    )


@router.get("/config-schools")
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
    user_id: Annotated[str, Path(alias="id")],
    school: str,
    user_patch_data: APIUserPatchRequest,
    users_patch_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
) -> CreateUserResponse:
    patch_data = UserPatchRequest(
        identifier=user_id,
        school=school,
        attributes=UserPatchAttributes(**user_patch_data.model_dump(exclude_unset=True)),
    )
    return await business_logic.patch_user(users_patch_adapter, representation_adapter, patch_data)


# currently a mock
@router.get("/config/users/add")
def get_user_add_config(school: str) -> AddUsersConfig:  # pragma: no cover
    return AddUsersConfig(
        pages=[
            PageConfig(
                label="Add user",
                name="useradd",
                fieldsets=[
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="School",
                            name="school",
                            description="School of the user",
                            hint="School",
                            required=True,
                            access=AttributeAccess.READ,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="Last name",
                            name="last_name",
                            description="Last name of the user",
                            hint="Last name",
                            required=True,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="First name",
                            name="first_name",
                            description="First name of the user",
                            hint="First name",
                            required=True,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="Username",
                            name="username",
                            description="Username of the user",
                            hint="Username",
                            required=False,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputPassword,
                        props=dict(
                            label="Password",
                            name="password",
                            description="Password of the user",
                            hint="Password",
                            required=False,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UMultiSelect,
                        props=dict(
                            label="School classes",
                            name="school_classes",
                            description="School classes of the user",
                            hint="School classes",
                            required=True,
                            access=AttributeAccess.WRITE,
                            columns=[
                                ColumnConfig(label="school class", attribute="class_name", order=0)
                            ],
                            rows=[
                                SchoolClassRow(
                                    id="school_class1",
                                    attributes=SchoolCLassRowAttributes(
                                        class_name=LabeledValue(
                                            label="school_class1", value="school_class1"
                                        )
                                    ),
                                ),
                                SchoolClassRow(
                                    id="school_class2",
                                    attributes=SchoolCLassRowAttributes(
                                        class_name=LabeledValue(
                                            label="school_class1", value="school_class2"
                                        )
                                    ),
                                ),
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.USelect,
                        props=dict(
                            label="Roles",
                            name="roles",
                            description="Roles of the user",
                            hint="Roles",
                            required=True,
                            access=AttributeAccess.WRITE,
                            options=[
                                {"label": "student", "value": "Student"},
                                {"label": "Teacher", "value": "teacher"},
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputCheckbox,
                        props=dict(
                            label="Disabled",
                            name="disabled",
                            description="Disabled",
                            hint="Disabled",
                            required=False,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                ],
            )
        ]
    )


# currently a mock
@router.get("/config/users/edit")
def get_user_edit_config(
    user_id: Annotated[str, Query(alias="id")], school: str
) -> EditUsersConfig:  # pragma: no cover
    return EditUsersConfig(
        id="user1",
        user={  # Sending only partial data on purpose for testing
            "username": "User 1",
            "first_name": "Max",
            "last_name": "Mustermann",
            "school": school,
            "school_classes": "school_class1",
        },
        pages=[
            PageConfig(
                label="Edit user",
                name="useredit",
                fieldsets=[
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="School",
                            name="school",
                            description="School of the user",
                            hint="School",
                            required=True,
                            access=AttributeAccess.READ,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="Last name",
                            name="last_name",
                            description="Last name of the user",
                            hint="Last name",
                            required=True,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="First name",
                            name="first_name",
                            description="First name of the user",
                            hint="First name",
                            required=True,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputText,
                        props=dict(
                            label="Username",
                            name="username",
                            description="Username of the user",
                            hint="Username",
                            required=False,
                            access=AttributeAccess.WRITE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputPassword,
                        props=dict(
                            label="Password",
                            name="password",
                            description="Password of the user",
                            hint="Password",
                            required=False,
                            access=AttributeAccess.NONE,
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UMultiSelect,
                        props=dict(
                            label="School classes",
                            name="school_classes",
                            description="School classes of the user",
                            hint="School classes",
                            required=True,
                            access=AttributeAccess.WRITE,
                            columns=[
                                ColumnConfig(label="school class", attribute="class_name", order=0)
                            ],
                            rows=[
                                SchoolClassRow(
                                    id="school_class1",
                                    attributes=SchoolCLassRowAttributes(
                                        class_name=LabeledValue(
                                            label="school_class1", value="school_class1"
                                        )
                                    ),
                                ),
                                SchoolClassRow(
                                    id="school_class2",
                                    attributes=SchoolCLassRowAttributes(
                                        class_name=LabeledValue(
                                            label="school_class1", value="school_class2"
                                        )
                                    ),
                                ),
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.USelect,
                        props=dict(
                            label="Roles",
                            name="roles",
                            description="Roles of the user",
                            hint="Roles",
                            required=True,
                            access=AttributeAccess.READ,
                            options=[
                                {"label": "student", "value": "Student"},
                                {"label": "Teacher", "value": "teacher"},
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UInputCheckbox,
                        props=dict(
                            label="Disabled",
                            name="disabled",
                            description="Disabled",
                            hint="Disabled",
                            required=False,
                            access=AttributeAccess.READ,
                        ),
                    ),
                ],
            )
        ],
    )


@router.delete("/users/{identifier}", status_code=204)
async def delete_user(
    identifier: str, users_delete_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort))
) -> None:
    return await business_logic.delete_user(users_delete_adapter, identifier)
