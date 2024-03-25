# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from . import business_logic
from .adapter_registry import port_dep
from .adapters.api import (
    FastAPIAddConfigRepresentationAdapter,
    FastAPIEditConfigRepresentationAdapter,
    FastAPISchoolsRepresentationAdapter,
    FastAPIUsersRepresentationAdapter,
)
from .api_models import (
    AddUsersConfig,
    APIUserPatchRequest,
    ColumnConfig,
    CreateUserResponse,
    EditUsersConfig,
    FormatterChoice,
    ListSchoolsResponse,
    ListUsersConfig,
    ListUsersResponse,
    UserCreateRequest,
)
from .constants import API_PREFIX
from .errors import CreationError, ObjectNotFoundError
from .models import UserPatchAttributes, UserPatchRequest, UsersGetRequest
from .ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
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


@router.patch("/users/{id}")
async def patch_user(
    request: Request,
    id: str,
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
        identifier=id,
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
    schools_get_adapter: SchoolsPersistencePort = Depends(port_dep(SchoolsPersistencePort)),
    school_classes_persistence_port: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    representation_adapter: FastAPIAddConfigRepresentationAdapter = Depends(
        port_dep(AddConfigRepresentationPort, adapter_cls=FastAPIAddConfigRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> AddUsersConfig:
    return await business_logic.get_user_add_config(
        schools_get_adapter, school_classes_persistence_port, representation_adapter, school
    )


@router.get("/config/users/edit")
async def get_user_edit_config(
    request: Request,
    id: str,
    school: str,
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    user_representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
    schools_get_adapter: SchoolsPersistencePort = Depends(port_dep(SchoolsPersistencePort)),
    school_classes_persistence_port: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    representation_adapter: FastAPIEditConfigRepresentationAdapter = Depends(
        port_dep(EditConfigRepresentationPort, adapter_cls=FastAPIEditConfigRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
) -> EditUsersConfig:
    actor_id = await authentication_port.get_authenticated_id(request)
    try:
        return await business_logic.get_user_edit_config(
            users_get_adapter,
            user_representation_adapter,
            schools_get_adapter,
            school_classes_persistence_port,
            representation_adapter,
            permissions_port,
            actor_id,
            id,
            school,
        )
    except ObjectNotFoundError:
        raise HTTPException(status_code=404, detail="User not found in school")


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
