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
    AttributeAccess,
    ColumnConfig,
    CreateUserResponse,
    CreateUserResponseUser,
    EditUsersConfig,
    Fieldset,
    FormatterChoice,
    LabeledValue,
    ListSchoolsResponse,
    ListUserAttribute,
    ListUserFixedAttributes,
    ListUsersConfig,
    ListUsersResponse,
    PageConfig,
    SchoolClassesConfig,
    SchoolClassRow,
    SchoolCLassRowAttributes,
    UserCreateRequest,
    UserPatchRequest,
    Watcher,
    WidgetType,
)
from .constants import API_PREFIX
from .errors import CreationError
from .models import UsersGetRequest
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
    user: UserCreateRequest,
    users_post_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
) -> CreateUserResponse:
    try:
        return await business_logic.create_user(users_post_adapter, representation_adapter, user)
    except CreationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Currently a mock. Response model should be renamed with proper implementation
@router.patch("/users/{id}")
def patch_user(
    user_id: Annotated[str, Path(alias="id")], user_patch_data: UserPatchRequest
) -> CreateUserResponse:  # pragma: no cover
    return CreateUserResponse(
        user=CreateUserResponseUser(
            id=user_id,
            attributes=ListUserFixedAttributes(
                **{
                    "last_name": ListUserAttribute[str](value="Mustermann", access=AttributeAccess.READ),
                    "first_name": ListUserAttribute[str](value="Max", access=AttributeAccess.READ),
                    "username": ListUserAttribute[str](
                        value="max.mustermann", access=AttributeAccess.READ
                    ),
                    "activated": ListUserAttribute[bool](value=True, access=AttributeAccess.READ),
                    "schools": ListUserAttribute[list[str]](
                        value=["school1"], access=AttributeAccess.READ
                    ),
                    "classes": ListUserAttribute[list[str]](
                        value=["school_class1"], access=AttributeAccess.READ
                    ),
                    "roles": ListUserAttribute[list[str]](
                        value=["teacher"], access=AttributeAccess.READ
                    ),
                },
            ),
        )
    )


# currently a mock
@router.get("/config/classes")
def get_school_classes(school: str) -> SchoolClassesConfig:  # pragma: no cover
    return SchoolClassesConfig(
        rows=[
            SchoolClassRow(
                id="school_class1",
                attributes=SchoolCLassRowAttributes(
                    class_name=LabeledValue(label="school_class1", value="school_class1")
                ),
            ),
            SchoolClassRow(
                id="school_class2",
                attributes=SchoolCLassRowAttributes(
                    class_name=LabeledValue(label="school_class1", value="school_class2")
                ),
            ),
        ]
    )


# currently a mock
@router.get("/config/users/add")
def get_user_add_config() -> AddUsersConfig:  # pragma: no cover
    return AddUsersConfig(
        pages=[
            PageConfig(
                label="Add user",
                name="useradd",
                fieldsets=[
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
                        type=WidgetType.USelect,
                        props=dict(
                            label="School",
                            name="school",
                            description="School of the user",
                            hint="School",
                            required=True,
                            access=AttributeAccess.WRITE,
                            options=[
                                {"label": "school1", "value": "school1"},
                                {"label": "school2", "value": "school2"},
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UMultiSelect,
                        watches=[Watcher(fields=["school"], callback_url="/config/classes")],
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
                            rows=[],
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
    user_id: Annotated[str, Query(alias="id")]
) -> EditUsersConfig:  # pragma: no cover
    return EditUsersConfig(
        id="user1",
        user={  # Sending only partial data on purpose for testing
            "username": "User 1",
            "first_name": "Max",
            "last_name": "Mustermann",
            "school": "school1",
            "school_classes": "school_class1",
        },
        pages=[
            PageConfig(
                label="Add user",
                name="useradd",
                fieldsets=[
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
                        type=WidgetType.USelect,
                        props=dict(
                            label="School",
                            name="school",
                            description="School of the user",
                            hint="School",
                            required=True,
                            access=AttributeAccess.READ,
                            options=[
                                {"label": "school1", "value": "school1"},
                                {"label": "school2", "value": "school2"},
                            ],
                        ),
                    ),
                    Fieldset(
                        type=WidgetType.UMultiSelect,
                        watches=[Watcher(fields=["school"], callback_url="/config/classes")],
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
                            rows=[],
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
