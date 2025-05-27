# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only


from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from . import business_logic
from .adapter_registry import port_dep
from .adapters.api import (
    FastAPIAddConfigRepresentationAdapter,
    FastAPIEditConfigRepresentationAdapter,
    FastAPIListConfigRepresentationAdapter,
    FastAPISchoolClassesRepresentationAdapter,
    FastAPISchoolsRepresentationAdapter,
    FastAPIUsersRepresentationAdapter,
    FastAPIWorkGroupsRepresentationAdapter,
)
from .api_models import (
    AddUsersConfig,
    APIUserPatchRequest,
    CreateUserResponse,
    EditUsersConfig,
    ListSchoolClassesResponse,
    ListSchoolsResponse,
    ListUsersConfig,
    ListUsersResponse,
    ListWorkGroupsResponse,
    UserCreateRequest,
)
from .constants import API_PREFIX
from .errors import CreationError, ObjectNotFoundError
from .lang import _, get_lang
from .models import UserPatchAttributes, UserPatchRequest, UsersGetRequest
from .ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
    FastAPIAuthenticationPort,
    ListConfigRepresentationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolClassesRepresentationPort,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UsersPersistencePort,
    UsersRepresentationPort,
    WorkGroupsPersistencePort,
    WorkGroupsRepresentationPort,
)

router = APIRouter(prefix=API_PREFIX)


@router.get("/config/users/list")
def get_users_config(
    representation_adapter: FastAPIListConfigRepresentationAdapter = Depends(
        port_dep(ListConfigRepresentationPort, adapter_cls=FastAPIListConfigRepresentationAdapter)
    ),
    lang: str = Depends(get_lang),
) -> ListUsersConfig:
    return representation_adapter.list_config_representation(lang)


@router.get("/users")
async def get_users(
    request: Request,
    school: str,
    school_classes: Annotated[list[str], Query(default_factory=list)],
    work_groups: Annotated[list[str], Query(default_factory=list)],
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    schools_get_adapter: SchoolsPersistencePort = Depends(port_dep(SchoolsPersistencePort)),
    school_classes_get_adapter: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    work_groups_get_adapter: WorkGroupsPersistencePort = Depends(port_dep(WorkGroupsPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    lang: str = Depends(get_lang),
) -> ListUsersResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.get_users(
        users_get_adapter,
        schools_get_adapter,
        school_classes_get_adapter,
        work_groups_get_adapter,
        representation_adapter,
        permissions_port,
        actor_id,
        UsersGetRequest(school=school, school_classes=school_classes, work_groups=work_groups),
        lang,
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
    lang: str = Depends(get_lang),
) -> ListSchoolsResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.get_schools(
        schools_get_adapter, representation_adapter, permissions_port, users_get_adapter, actor_id, lang
    )


@router.get("/config/school_classes")
async def get_school_classes(
    request: Request,
    school: str,
    school_classses_get_adapter: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    representation_adapter: FastAPISchoolClassesRepresentationAdapter = Depends(
        port_dep(SchoolClassesRepresentationPort, adapter_cls=FastAPISchoolClassesRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    lang: str = Depends(get_lang),
) -> ListSchoolClassesResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    # school_id = await request
    return await business_logic.get_school_classes(
        school_classses_get_adapter,
        representation_adapter,
        permissions_port,
        users_get_adapter,
        actor_id,
        school,
        lang,
    )


@router.get("/config/work_groups")
async def get_work_groups(
    request: Request,
    school: str,
    work_group_get_adapter: WorkGroupsPersistencePort = Depends(port_dep(WorkGroupsPersistencePort)),
    representation_adapter: FastAPIWorkGroupsRepresentationAdapter = Depends(
        port_dep(WorkGroupsRepresentationPort, adapter_cls=FastAPIWorkGroupsRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    lang: str = Depends(get_lang),
) -> ListWorkGroupsResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    # school_id = await request
    return await business_logic.get_work_groups(
        work_group_get_adapter,
        representation_adapter,
        permissions_port,
        users_get_adapter,
        actor_id,
        school,
        lang,
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
    lang: str = Depends(get_lang),
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
            lang,
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
    lang: str = Depends(get_lang),
) -> CreateUserResponse:
    actor_id = await authentication_port.get_authenticated_id(request)
    patch_data = UserPatchRequest(
        identifier=id,
        school=school,
        attributes=UserPatchAttributes(**user_patch_data.model_dump(exclude_unset=True)),
    )
    return await business_logic.patch_user(
        users_patch_adapter, representation_adapter, permissions_port, actor_id, patch_data, lang
    )


@router.get("/config/users/add")
async def get_user_add_config(
    request: Request,
    school: str,
    schools_get_adapter: SchoolsPersistencePort = Depends(port_dep(SchoolsPersistencePort)),
    school_classes_persistence_port: SchoolClassesPersistencePort = Depends(
        port_dep(SchoolClassesPersistencePort)
    ),
    work_groups_persistence_port: WorkGroupsPersistencePort = Depends(
        port_dep(WorkGroupsPersistencePort)
    ),
    representation_adapter: FastAPIAddConfigRepresentationAdapter = Depends(
        port_dep(AddConfigRepresentationPort, adapter_cls=FastAPIAddConfigRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    lang: str = Depends(get_lang),
) -> AddUsersConfig:
    return await business_logic.get_user_add_config(
        schools_get_adapter,
        school_classes_persistence_port,
        work_groups_persistence_port,
        representation_adapter,
        school,
        lang,
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
    work_groups_persistence_port: WorkGroupsPersistencePort = Depends(
        port_dep(WorkGroupsPersistencePort)
    ),
    representation_adapter: FastAPIEditConfigRepresentationAdapter = Depends(
        port_dep(EditConfigRepresentationPort, adapter_cls=FastAPIEditConfigRepresentationAdapter)
    ),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    lang: str = Depends(get_lang),
) -> EditUsersConfig:
    actor_id = await authentication_port.get_authenticated_id(request)
    try:
        return await business_logic.get_user_edit_config(
            users_get_adapter,
            user_representation_adapter,
            schools_get_adapter,
            school_classes_persistence_port,
            work_groups_persistence_port,
            representation_adapter,
            permissions_port,
            actor_id,
            id,
            school,
            lang,
        )
    except ObjectNotFoundError:
        raise HTTPException(
            status_code=404, detail=_("The user was not found in the school.", lang=lang)
        )


@router.delete("/users/{identifier}", status_code=204)
async def delete_user(
    request: Request,
    identifier: str,
    users_delete_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    authentication_port: FastAPIAuthenticationPort = Depends(port_dep(FastAPIAuthenticationPort)),
    permissions_port: PermissionsPort = Depends(port_dep(PermissionsPort)),
    lang: str = Depends(get_lang),
) -> None:
    actor_id = await authentication_port.get_authenticated_id(request)
    return await business_logic.delete_user(
        users_delete_adapter, permissions_port, actor_id, identifier, lang
    )
