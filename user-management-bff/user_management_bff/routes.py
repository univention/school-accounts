# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from fastapi import APIRouter

from .api_models import ColumnConfig, FormatterChoice, ListUsersConfig
from .constants import API_PREFIX

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
