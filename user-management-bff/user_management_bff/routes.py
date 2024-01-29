# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from fastapi import APIRouter, Depends

from . import business_logic
from .adapter_registry import port_dep
from .adapters.api import FastAPIUsersRepresentationAdapter
from .api_models import (
    ColumnConfig,
    FormatterChoice,
    ListUsersConfig,
    ListUsersResponse,
)
from .constants import API_PREFIX
from .models import UsersGetRequest
from .ports import UsersPersistencePort, UsersRepresentationPort

router = APIRouter(prefix=API_PREFIX)

COLUMN_CONFIGS: list[dict[str, Any]] = [
    {
        "label": "Last name",
        "attribute": "last_name",
    },
    {
        "label": "First name",
        "attribute": "first_name",
    },
    {
        "label": "Username",
        "attribute": "username",
    },
    {
        "label": "Schools",
        "attribute": "schools",
        "formatter": FormatterChoice.LIST,
    },
    {
        "label": "Activation state",
        "attribute": "disabled",
    },
    {
        "label": "Roles",
        "attribute": "ucsschool_roles",
        "formatter": FormatterChoice.LIST,
    },
]


@router.get("/config-users")
def get_users_config() -> ListUsersConfig:
    return ListUsersConfig(
        columns=[ColumnConfig(**column, order=index) for index, column in enumerate(COLUMN_CONFIGS)]
    )


@router.get("/users")
def get_users(
    school: str,
    users_get_adapter: UsersPersistencePort = Depends(port_dep(UsersPersistencePort)),
    representation_adapter: FastAPIUsersRepresentationAdapter = Depends(
        port_dep(UsersRepresentationPort, adapter_cls=FastAPIUsersRepresentationAdapter)
    ),
) -> ListUsersResponse:
    return business_logic.get_users(
        users_get_adapter, representation_adapter, UsersGetRequest(school=school)
    )
