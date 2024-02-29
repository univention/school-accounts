# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from fastapi import APIRouter, Depends, Request

from . import business_logic
from .adapter_registry import port_dep
from .adapters.api import FastAPISchoolsRepresentationAdapter, FastAPIUsersRepresentationAdapter
from .api_models import (
    ColumnConfig,
    FormatterChoice,
    ListSchoolsResponse,
    ListUsersConfig,
    ListUsersResponse,
)
from .constants import API_PREFIX
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
        "attribute": "ucsschool_roles",
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
